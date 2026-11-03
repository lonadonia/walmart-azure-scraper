"""the store's product-detail work and its scheduled occurrences survive across runs: saved observations of a
product's own page (``detail_observations``), a ``detail`` kind on the follow-up queue, and an identity for
every scheduled occurrence (``schedule_occurrences``)

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-31 18:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(op.f("ck_follow_up_queue_kind"), "follow_up_queue", type_="check")
    op.create_check_constraint(
        op.f("ck_follow_up_queue_kind"), "follow_up_queue", "kind IN ('sponsored', 'variant', 'detail')"
    )
    op.create_table(
        "detail_observations",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("store_id", sa.String(length=26), nullable=False),
        sa.Column("item_id", sa.String(length=20), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("run_id", sa.String(length=26), nullable=False),
        sa.Column("page_fetch_id", sa.String(length=26), nullable=True),
        sa.Column("source_revision", sa.Text(), nullable=True),
        sa.Column("origin", sa.String(length=16), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("body_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("upc", sa.String(length=14), nullable=True),
        sa.Column("upc_path", sa.Text(), nullable=True),
        sa.Column("size_statements", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('extracted', 'absent_in_source')", name=op.f("ck_detail_observations_status")
        ),
        sa.CheckConstraint("origin IN ('fetched', 'imported')", name=op.f("ck_detail_observations_origin")),
        sa.ForeignKeyConstraint(
            ["store_id"], ["stores.id"], name=op.f("fk_detail_observations_store_id_stores")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_detail_observations")),
        sa.UniqueConstraint("store_id", "item_id", "body_sha256", name="uq_detail_observations_page"),
    )
    op.create_index(
        "ix_detail_observations_item", "detail_observations", ["store_id", "item_id", "observed_at"]
    )
    op.create_table(
        "schedule_occurrences",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("store_id", sa.String(length=26), nullable=False),
        sa.Column("day", sa.String(length=10), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("noticed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("run_id", sa.String(length=26), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_missed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "state IN ('due', 'deferred', 'running', 'completed', 'superseded')",
            name=op.f("ck_schedule_occurrences_state"),
        ),
        sa.ForeignKeyConstraint(
            ["store_id"], ["stores.id"], name=op.f("fk_schedule_occurrences_store_id_stores")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_schedule_occurrences")),
        sa.UniqueConstraint("store_id", "day", name="uq_schedule_occurrences_day"),
    )
    op.create_index("ix_schedule_occurrences_store_state", "schedule_occurrences", ["store_id", "state"])


def downgrade() -> None:
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM detail_observations) "
        "OR EXISTS (SELECT 1 FROM schedule_occurrences) "
        "OR EXISTS (SELECT 1 FROM follow_up_queue WHERE kind = 'detail') THEN "
        "RAISE EXCEPTION 'detail work or occurrences are recorded: keep revision 0006'; END IF; END $$;"
    )
    op.drop_index("ix_schedule_occurrences_store_state", table_name="schedule_occurrences")
    op.drop_table("schedule_occurrences")
    op.drop_index("ix_detail_observations_item", table_name="detail_observations")
    op.drop_table("detail_observations")
    op.drop_constraint(op.f("ck_follow_up_queue_kind"), "follow_up_queue", type_="check")
    op.create_check_constraint(
        op.f("ck_follow_up_queue_kind"), "follow_up_queue", "kind IN ('sponsored', 'variant')"
    )
