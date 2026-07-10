"""digest.act_analysis — insert-only LLM analyses, versioned by prompt

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "act_analysis",
        sa.Column("pdf_url", sa.String(), nullable=False),
        sa.Column("prompt_version", sa.String(length=8), nullable=False),
        sa.Column("themes", ARRAY(sa.String(length=16)), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("summary_plain", sa.Text(), nullable=False),
        sa.Column("ungrounded_numbers", ARRAY(sa.String(length=32)), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["pdf_url"], ["raw.gazette_item.pdf_url"], name="fk_act_analysis_pdf_url_gazette_item"
        ),
        sa.PrimaryKeyConstraint("pdf_url", "prompt_version", name="pk_act_analysis"),
        schema="digest",
    )


def downgrade() -> None:
    op.drop_table("act_analysis", schema="digest")
