"""initial schema: raw/digest/evals/ops + raw.gazette_item + raw.act_text

Revision ID: 0001
Revises:
Create Date: 2026-07-10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMAS = ("raw", "digest", "evals", "ops")


def upgrade() -> None:
    for schema in SCHEMAS:
        op.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

    op.create_table(
        "gazette_item",
        sa.Column("pdf_url", sa.String(), nullable=False),
        sa.Column("act_title", sa.String(length=200), nullable=False),
        sa.Column("issue_number", sa.String(length=20), nullable=False),
        sa.Column("series", sa.String(length=4), nullable=False),
        sa.Column("supplement", sa.String(length=40), nullable=True),
        sa.Column("pub_date", sa.Date(), nullable=False),
        sa.Column("summary_raw", sa.Text(), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("pdf_url", name="pk_gazette_item"),
        schema="raw",
    )
    op.create_table(
        "act_text",
        sa.Column("pdf_url", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("n_chars", sa.Integer(), nullable=False),
        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["pdf_url"], ["raw.gazette_item.pdf_url"], name="fk_act_text_pdf_url_gazette_item"
        ),
        sa.PrimaryKeyConstraint("pdf_url", name="pk_act_text"),
        schema="raw",
    )


def downgrade() -> None:
    op.drop_table("act_text", schema="raw")
    op.drop_table("gazette_item", schema="raw")
