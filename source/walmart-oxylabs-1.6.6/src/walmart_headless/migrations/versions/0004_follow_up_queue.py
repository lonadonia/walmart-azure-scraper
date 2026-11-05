"""the store's follow-up queue: product pages of sponsored-only products and variant siblings a run named and
no run has yet read to a decision, kept across runs so that a pilot budget, a pause or an inaccessible page
never drops one for good (``follow_up_queue``)

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-27 12:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "follow_up_queue",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("store_id", sa.String(length=26), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("item_id", sa.String(length=20), nullable=False),
        sa.Column("lineage", sa.String(length=16), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("listing", sa.String(length=128), nullable=True),
        sa.Column("named_by", sa.String(length=20), nullable=True),
        sa.Column("option", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column("first_seen_run", sa.String(length=26), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_run", sa.String(length=26), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("runs_seen", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("last_status", sa.String(length=16), nullable=True),
        sa.Column("last_reason", sa.Text(), nullable=True),
        sa.Column("last_run", sa.String(length=26), nullable=True),
        sa.Column("last_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pages_read", sa.Integer(), nullable=False),
        sa.CheckConstraint("kind IN ('sponsored', 'variant')", name=op.f("ck_follow_up_queue_kind")),
        sa.CheckConstraint("state IN ('pending', 'resolved')", name=op.f("ck_follow_up_queue_state")),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], name=op.f("fk_follow_up_queue_store_id_stores")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_follow_up_queue")),
        sa.UniqueConstraint("store_id", "kind", "item_id", "lineage", name="uq_follow_up_queue_item"),
    )
    op.create_index("ix_follow_up_queue_store_state", "follow_up_queue", ["store_id", "state"], unique=False)


def downgrade() -> None:
    # Pending follow-ups would be lost with the table: never dropped while it holds any.
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM follow_up_queue WHERE state = 'pending') THEN "
        "RAISE EXCEPTION 'pending follow-ups are queued: keep revision 0004'; END IF; END $$;"
    )
    op.drop_index("ix_follow_up_queue_store_state", table_name="follow_up_queue")
    op.drop_table("follow_up_queue")
