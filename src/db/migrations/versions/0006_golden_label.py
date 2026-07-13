"""evals.golden_label — hand-labelled themes per act (blind ground truth)

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "golden_label",
        sa.Column("pdf_url", sa.String(), nullable=False),
        sa.Column("themes", ARRAY(sa.String(length=16)), nullable=False),
        sa.Column(
            "labelled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["pdf_url"], ["raw.gazette_item.pdf_url"], name="fk_golden_label_pdf_url_gazette_item"
        ),
        sa.PrimaryKeyConstraint("pdf_url", name="pk_golden_label"),
        schema="evals",
    )


def downgrade() -> None:
    op.drop_table("golden_label", schema="evals")
