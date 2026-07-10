"""ORM models. Layers are Postgres schemas: raw / digest / evals / ops (all UTC).

Idempotency rule inherited from energia-forecast: ``first_seen_at`` is written on INSERT and
never touched by upserts — it is the "when did we first see this act announced" audit anchor.
The natural key of an act announcement is its official PDF URL (stable, page-range based).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class GazetteItem(Base):
    """raw.gazette_item — one act as announced in the daily Série I feed."""

    __tablename__ = "gazette_item"
    __table_args__ = {"schema": "raw"}  # noqa: RUF012 — SQLAlchemy config, not a mutable default

    pdf_url: Mapped[str] = mapped_column(String, primary_key=True)

    act_title: Mapped[str] = mapped_column(String(200), nullable=False)
    issue_number: Mapped[str] = mapped_column(String(20), nullable=False)
    series: Mapped[str] = mapped_column(String(4), nullable=False)
    supplement: Mapped[str | None] = mapped_column(String(40), nullable=True)
    pub_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    summary_raw: Mapped[str] = mapped_column(Text, nullable=False)

    first_seen_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ActText(Base):
    """raw.act_text — extracted, normalised text of an act's official PDF (immutable)."""

    __tablename__ = "act_text"
    __table_args__ = {"schema": "raw"}  # noqa: RUF012 — SQLAlchemy config, not a mutable default

    pdf_url: Mapped[str] = mapped_column(
        String, ForeignKey("raw.gazette_item.pdf_url"), primary_key=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    n_chars: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
