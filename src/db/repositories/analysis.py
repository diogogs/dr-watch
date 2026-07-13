"""Write side of digest.act_analysis (insert-only) + the work queue query."""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import Row, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.db.models import ActAnalysis, ActText, DayGrouping, GazetteItem


def acts_missing_analysis(
    session: Session, prompt_version: str
) -> list[Row[tuple[str, str, str, str, dt.date]]]:
    """(pdf_url, act_title, summary_raw, text, pub_date) for acts with text but no analysis."""
    stmt = (
        select(
            GazetteItem.pdf_url,
            GazetteItem.act_title,
            GazetteItem.summary_raw,
            ActText.text,
            GazetteItem.pub_date,
        )
        .join(ActText, ActText.pdf_url == GazetteItem.pdf_url)
        .outerjoin(
            ActAnalysis,
            (ActAnalysis.pdf_url == GazetteItem.pdf_url)
            & (ActAnalysis.prompt_version == prompt_version),
        )
        .where(ActAnalysis.pdf_url.is_(None))
        .order_by(GazetteItem.pub_date, GazetteItem.pdf_url)
    )
    return list(session.execute(stmt).all())


def acts_for_grouping(
    session: Session, pub_date: dt.date, prompt_version: str
) -> list[Row[tuple[str, str, str | None]]]:
    """(pdf_url, act_title, headline) of a day's analysed acts, in stable order."""
    stmt = (
        select(GazetteItem.pdf_url, GazetteItem.act_title, ActAnalysis.headline)
        .join(ActAnalysis, ActAnalysis.pdf_url == GazetteItem.pdf_url)
        .where(GazetteItem.pub_date == pub_date, ActAnalysis.prompt_version == prompt_version)
        .order_by(GazetteItem.pdf_url)
    )
    return list(session.execute(stmt).all())


def analysed_days_without_grouping(session: Session, prompt_version: str) -> list[dt.date]:
    """Days that have analyses at this prompt version but no grouping row yet."""
    stmt = (
        select(GazetteItem.pub_date)
        .join(ActAnalysis, ActAnalysis.pdf_url == GazetteItem.pdf_url)
        .outerjoin(
            DayGrouping,
            (DayGrouping.pub_date == GazetteItem.pub_date)
            & (DayGrouping.prompt_version == prompt_version),
        )
        .where(ActAnalysis.prompt_version == prompt_version, DayGrouping.id.is_(None))
        .distinct()
        .order_by(GazetteItem.pub_date)
    )
    return list(session.execute(stmt).scalars().all())


def insert_day_grouping(
    session: Session,
    *,
    pub_date: dt.date,
    prompt_version: str,
    groups: list[dict[str, Any]],
    model_name: str,
) -> None:
    """Append a new grouping version for the day; earlier versions are never rewritten."""
    session.add(
        DayGrouping(
            pub_date=pub_date, prompt_version=prompt_version, groups=groups, model_name=model_name
        )
    )


def insert_analysis(
    session: Session,
    *,
    pdf_url: str,
    prompt_version: str,
    themes: list[str],
    rationale: str,
    headline: str | None,
    summary_plain: str,
    ungrounded: list[str],
    model_name: str,
) -> None:
    """Insert once per (act, prompt version); a published analysis is never rewritten."""
    stmt = pg_insert(ActAnalysis).values(
        pdf_url=pdf_url,
        prompt_version=prompt_version,
        themes=themes,
        rationale=rationale,
        headline=headline,
        summary_plain=summary_plain,
        ungrounded_numbers=ungrounded,
        model_name=model_name,
    )
    session.execute(stmt.on_conflict_do_nothing(index_elements=["pdf_url", "prompt_version"]))
