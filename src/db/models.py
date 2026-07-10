"""ORM models. Layers are Postgres schemas: raw / digest / evals / ops (all UTC).

Idempotency rule inherited from energia-forecast: ``first_seen_at`` is written on INSERT and
never touched by upserts — it is the "when did we first see this act announced" audit anchor.
The natural key of an act announcement is its official PDF URL (stable, page-range based).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
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


class ActAnalysis(Base):
    """digest.act_analysis — the LLM's take on one act, INSERT-ONLY (charter principle 5).

    Keyed by (pdf_url, prompt_version): re-running a day never rewrites a published analysis,
    and a deliberate prompt upgrade creates NEW rows instead of silently editing history.
    ``ungrounded_numbers`` is the deterministic verify step's output — numbers that appear in
    the summary but not in the source; non-empty means the summary is flagged, not published.
    """

    __tablename__ = "act_analysis"
    __table_args__ = {"schema": "digest"}  # noqa: RUF012 — SQLAlchemy config

    pdf_url: Mapped[str] = mapped_column(
        String, ForeignKey("raw.gazette_item.pdf_url"), primary_key=True
    )
    prompt_version: Mapped[str] = mapped_column(String(8), primary_key=True)

    themes: Mapped[list[str]] = mapped_column(ARRAY(String(16)), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    summary_plain: Mapped[str] = mapped_column(Text, nullable=False)
    ungrounded_numbers: Mapped[list[str]] = mapped_column(ARRAY(String(32)), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
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
