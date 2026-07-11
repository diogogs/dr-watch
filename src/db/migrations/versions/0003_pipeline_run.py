"""evals.pipeline_run — append-only run log (coverage, grounding, citation checks)

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pipeline_run",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("prompt_version", sa.String(length=8), nullable=False),
        sa.Column("queued", sa.Integer(), nullable=False),
        sa.Column("analysed", sa.Integer(), nullable=False),
        sa.Column("flagged", sa.Integer(), nullable=False),
        sa.Column("failed", sa.Integer(), nullable=False),
        sa.Column("deferred", sa.Integer(), nullable=False),
        sa.Column("citation_ok", sa.Integer(), nullable=False),
        sa.Column("citation_total", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_pipeline_run"),
        schema="evals",
    )


def downgrade() -> None:
    op.drop_table("pipeline_run", schema="evals")
