"""digest.day_grouping — append-only subject clusters per day (presentation-level)

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "day_grouping",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("pub_date", sa.Date(), nullable=False),
        sa.Column("prompt_version", sa.String(length=8), nullable=False),
        sa.Column("groups", JSONB(), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_day_grouping"),
        schema="digest",
    )
    op.create_index(
        "ix_day_grouping_date_version",
        "day_grouping",
        ["pub_date", "prompt_version"],
        schema="digest",
    )


def downgrade() -> None:
    op.drop_index("ix_day_grouping_date_version", "day_grouping", schema="digest")
    op.drop_table("day_grouping", schema="digest")
