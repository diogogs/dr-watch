"""Write side of the raw layer. Callers own the transaction (commit)."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.db.models import ActText, GazetteItem
from src.ingestion.rss import GazetteItem as FeedItem


def upsert_gazette_items(session: Session, items: Iterable[FeedItem]) -> int:
    """Upsert feed items by pdf_url. first_seen_at is written on INSERT and never touched;
    the announced fields refresh on conflict (the feed may correct a summary within the day)."""
    rows = [
        {
            "pdf_url": i.pdf_url,
            "act_title": i.act_title,
            "issue_number": i.issue_number,
            "series": i.series,
            "supplement": i.supplement,
            "pub_date": i.pub_date,
            "summary_raw": i.summary_raw,
        }
        for i in items
    ]
    if not rows:
        return 0
    stmt = pg_insert(GazetteItem).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["pdf_url"],
        set_={
            "act_title": stmt.excluded.act_title,
            "issue_number": stmt.excluded.issue_number,
            "series": stmt.excluded.series,
            "supplement": stmt.excluded.supplement,
            "pub_date": stmt.excluded.pub_date,
            "summary_raw": stmt.excluded.summary_raw,
            "last_seen_at": func.now(),
        },
    )
    session.execute(stmt)
    return len(rows)


def urls_missing_text(session: Session) -> list[str]:
    """Announced acts whose PDF text has not been extracted yet."""
    stmt = (
        select(GazetteItem.pdf_url)
        .outerjoin(ActText, ActText.pdf_url == GazetteItem.pdf_url)
        .where(ActText.pdf_url.is_(None))
        .order_by(GazetteItem.pub_date, GazetteItem.pdf_url)
    )
    return list(session.execute(stmt).scalars())


def insert_act_text(session: Session, pdf_url: str, text: str) -> None:
    """Insert extracted text once; the official PDF is immutable, so re-runs are no-ops."""
    stmt = pg_insert(ActText).values(pdf_url=pdf_url, text=text, n_chars=len(text))
    session.execute(stmt.on_conflict_do_nothing(index_elements=["pdf_url"]))
