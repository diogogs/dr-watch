"""Write side of digest.act_analysis (insert-only) + the work queue query."""

from __future__ import annotations

from sqlalchemy import Row, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.db.models import ActAnalysis, ActText, GazetteItem


def acts_missing_analysis(
    session: Session, prompt_version: str
) -> list[Row[tuple[str, str, str, str]]]:
    """(pdf_url, act_title, summary_raw, text) for acts with text but no analysis yet."""
    stmt = (
        select(GazetteItem.pdf_url, GazetteItem.act_title, GazetteItem.summary_raw, ActText.text)
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
