"""digest.act_analysis.headline — plain-language headline (prompt v1)

Nullable by design: act_analysis is insert-only, so v0 rows are history and stay as they
were published. v1 rows always carry a headline (the pipeline contract requires it).

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("act_analysis", sa.Column("headline", sa.Text(), nullable=True), schema="digest")


def downgrade() -> None:
    op.drop_column("act_analysis", "headline", schema="digest")
