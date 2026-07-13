"""ORM models. Layers are Postgres schemas: raw / digest / evals / ops (all UTC).

Idempotency rule inherited from energia-forecast: ``first_seen_at`` is written on INSERT and
never touched by upserts — it is the "when did we first see this act announced" audit anchor.
The natural key of an act announcement is its official PDF URL (stable, page-range based).
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Identity, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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
    # Nullable: v0 rows predate the headline (insert-only history is never backfilled).
    headline: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_plain: Mapped[str] = mapped_column(Text, nullable=False)
    ungrounded_numbers: Mapped[list[str]] = mapped_column(ARRAY(String(32)), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class DayGrouping(Base):
    """digest.day_grouping — subject clusters for one day's digest, APPEND-ONLY.

    Presentation-level only: grouping never merges content — each act keeps its own
    headline, summary and citation; a group just says which acts share a subject.
    ``groups`` is ``[{"label": str, "pdf_urls": [str, ...]}]`` (only groups of >= 2;
    empty list = grouping ran and found none). A day is re-grouped (new row) whenever
    new analyses land for it; the site reads the LATEST row per (pub_date, version),
    and a day with no row simply renders ungrouped — grouping can never break a digest.
    """

    __tablename__ = "day_grouping"
    __table_args__ = {"schema": "digest"}  # noqa: RUF012 — SQLAlchemy config

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    pub_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(8), nullable=False)
    groups: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PipelineRun(Base):
    """evals.pipeline_run — append-only log of every analysis run (the evals backbone).

    One row per execution: what was queued, analysed, flagged by the grounding check,
    deferred by the budget, failed hard — plus the citation check (do the official PDF
    links behind this run's analyses actually resolve?). The public evals page derives
    from these rows; nothing here is ever updated.
    """

    __tablename__ = "pipeline_run"
    __table_args__ = {"schema": "evals"}  # noqa: RUF012 — SQLAlchemy config

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    prompt_version: Mapped[str] = mapped_column(String(8), nullable=False)
    queued: Mapped[int] = mapped_column(Integer, nullable=False)
    analysed: Mapped[int] = mapped_column(Integer, nullable=False)
    flagged: Mapped[int] = mapped_column(Integer, nullable=False)
    failed: Mapped[int] = mapped_column(Integer, nullable=False)
    deferred: Mapped[int] = mapped_column(Integer, nullable=False)
    citation_ok: Mapped[int] = mapped_column(Integer, nullable=False)
    citation_total: Mapped[int] = mapped_column(Integer, nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class GoldenLabel(Base):
    """evals.golden_label — the author's hand-labelled themes for one act (ground truth).

    Labelled BLIND: the labelling tool never shows the model's classification, so the
    golden set cannot inherit the model's mistakes (charter principle 2 — evals before
    prompts). ``themes`` is ordered: the first element is the primary theme. One row per
    act; re-labelling a mistake overwrites (this is eval input, not a published output).
    """

    __tablename__ = "golden_label"
    __table_args__ = {"schema": "evals"}  # noqa: RUF012 — SQLAlchemy config

    pdf_url: Mapped[str] = mapped_column(
        String, ForeignKey("raw.gazette_item.pdf_url"), primary_key=True
    )
    themes: Mapped[list[str]] = mapped_column(ARRAY(String(16)), nullable=False)
    labelled_at: Mapped[dt.datetime] = mapped_column(
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
