"""runs may be REPLAY runs (stored pages of an earlier LIVE run read again offline)

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-24 04:10:00
"""

from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(op.f("ck_runs_mode"), "runs", type_="check")
    op.create_check_constraint(op.f("ck_runs_mode"), "runs", "mode IN ('LIVE', 'FIXTURE', 'REPLAY')")


def downgrade() -> None:
    # Replay runs (and what refers to them) would break the earlier constraint: never deleted here.
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM runs WHERE mode = 'REPLAY') THEN "
        "RAISE EXCEPTION 'REPLAY runs exist: keep revision 0002'; END IF; END $$;"
    )
    op.drop_constraint(op.f("ck_runs_mode"), "runs", type_="check")
    op.create_check_constraint(op.f("ck_runs_mode"), "runs", "mode IN ('LIVE', 'FIXTURE')")
