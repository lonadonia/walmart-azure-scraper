"""provider ledger rows name their API product, segment and worker and carry a dollar figure; collection
segments record their number of workers and their measurements; a run may have follow-up tasks (product pages
of sponsored-only products and of variant siblings, read after every listing); sponsored placements are
recorded as observations of their own (``sponsored_card``), and a page's sponsored and organic placements
of one product are both kept as memberships (the unique key includes ``via``)

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-26 22:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


OLD_KINDS = (
    "preflight",
    "attest",
    "census",
    "listing_node",
    "pdp",
    "coupons_catalogue",
    "coupon_items",
    "assemble",
    "validate",
    "export",
)
NEW_KINDS = (*OLD_KINDS, "follow_up")
OLD_SOURCES = ("card", "pdp", "coupon_items")
NEW_SOURCES = (*OLD_SOURCES, "sponsored_card")


def _kinds(kinds: tuple[str, ...], column: str = "kind") -> str:
    return f"{column} IN (" + ", ".join(repr(k) for k in kinds) + ")"


def _membership_key(with_via: bool) -> None:
    op.drop_index("uq_memberships_key", table_name="memberships")
    op.create_index(
        "uq_memberships_key",
        "memberships",
        [
            "run_id",
            "upc",
            "category_source_id",
            sa.literal_column("coalesce(taxonomy_id, '')"),
            sa.literal_column("coalesce(coupon_id, '')"),
            "page_offset",
            *(["via"] if with_via else []),
        ],
        unique=True,
    )


def upgrade() -> None:
    op.drop_constraint(op.f("ck_tasks_kind"), "tasks", type_="check")
    op.create_check_constraint(op.f("ck_tasks_kind"), "tasks", _kinds(NEW_KINDS))
    op.drop_constraint(op.f("ck_product_observations_source"), "product_observations", type_="check")
    op.create_check_constraint(
        op.f("ck_product_observations_source"), "product_observations", _kinds(NEW_SOURCES, "source")
    )
    op.add_column("provider_usage", sa.Column("api_product", sa.String(64), nullable=True))
    op.add_column("provider_usage", sa.Column("segment_id", sa.String(26), nullable=True))
    op.add_column("provider_usage", sa.Column("worker", sa.String(64), nullable=True))
    op.add_column("provider_usage", sa.Column("cost_usd", sa.Float(), nullable=True))
    op.create_index("ix_provider_usage_segment_id", "provider_usage", ["segment_id"])
    op.add_column("collection_segments", sa.Column("workers", sa.Integer(), nullable=True))
    op.add_column(
        "collection_segments", sa.Column("stats", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    _membership_key(with_via=True)


def downgrade() -> None:
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM tasks WHERE kind = 'follow_up') THEN "
        "RAISE EXCEPTION 'follow-up tasks exist: keep revision 0003'; END IF; END $$;"
    )
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM product_observations WHERE source = 'sponsored_card') THEN "
        "RAISE EXCEPTION 'sponsored placements are recorded: keep revision 0003'; END IF; END $$;"
    )
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM memberships GROUP BY run_id, upc, category_source_id, "
        "coalesce(taxonomy_id, ''), coalesce(coupon_id, ''), page_offset HAVING count(*) > 1) THEN "
        "RAISE EXCEPTION 'a page has two placements of one product: keep revision 0003'; END IF; END $$;"
    )
    _membership_key(with_via=False)
    op.drop_constraint(op.f("ck_product_observations_source"), "product_observations", type_="check")
    op.create_check_constraint(
        op.f("ck_product_observations_source"), "product_observations", _kinds(OLD_SOURCES, "source")
    )
    op.drop_constraint(op.f("ck_tasks_kind"), "tasks", type_="check")
    op.create_check_constraint(op.f("ck_tasks_kind"), "tasks", _kinds(OLD_KINDS))
    op.drop_column("collection_segments", "stats")
    op.drop_column("collection_segments", "workers")
    op.drop_index("ix_provider_usage_segment_id", table_name="provider_usage")
    op.drop_column("provider_usage", "cost_usd")
    op.drop_column("provider_usage", "worker")
    op.drop_column("provider_usage", "segment_id")
    op.drop_column("provider_usage", "api_product")
