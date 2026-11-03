"""the options a result tile names when the run keeps no record from that tile (a repeated tile of a
product the run already recorded, or a sponsored tile) are recorded as observations of their own
(``tile_options``), so that the variant follow-up reads every item a result tile offers

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-27 18:00:00
"""

from __future__ import annotations

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


OLD_SOURCES = ("card", "pdp", "coupon_items", "sponsored_card")
NEW_SOURCES = (*OLD_SOURCES, "tile_options")


def _sources(sources: tuple[str, ...]) -> str:
    return "source IN (" + ", ".join(repr(s) for s in sources) + ")"


def upgrade() -> None:
    op.drop_constraint(op.f("ck_product_observations_source"), "product_observations", type_="check")
    op.create_check_constraint(
        op.f("ck_product_observations_source"), "product_observations", _sources(NEW_SOURCES)
    )


def downgrade() -> None:
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM product_observations WHERE source = 'tile_options') THEN "
        "RAISE EXCEPTION 'tile options are recorded: keep revision 0005'; END IF; END $$;"
    )
    op.drop_constraint(op.f("ck_product_observations_source"), "product_observations", type_="check")
    op.create_check_constraint(
        op.f("ck_product_observations_source"), "product_observations", _sources(OLD_SOURCES)
    )
