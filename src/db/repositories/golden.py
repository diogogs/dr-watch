"""Golden-set repository: what still needs a hand label, and writing labels."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Row, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.db.models import ActText, GazetteItem, GoldenLabel


def acts_missing_label(
    session: Session,
) -> list[Row[tuple[str, str, str, str, dt.date]]]:
    """(pdf_url, act_title, summary_raw, text, pub_date) for acts without a golden label,
    oldest first — the author labels the archive in publication order."""
    stmt = (
        select(
            GazetteItem.pdf_url,
            GazetteItem.act_title,
            GazetteItem.summary_raw,
            ActText.text,
            GazetteItem.pub_date,
        )
        .join(ActText, ActText.pdf_url == GazetteItem.pdf_url)
        .outerjoin(GoldenLabel, GoldenLabel.pdf_url == GazetteItem.pdf_url)
        .where(GoldenLabel.pdf_url.is_(None))
        .order_by(GazetteItem.pub_date, GazetteItem.pdf_url)
    )
    return list(session.execute(stmt).all())


def upsert_label(session: Session, *, pdf_url: str, themes: list[str]) -> None:
    """Write the author's label; re-labelling overwrites (eval input, not published output)."""
    stmt = pg_insert(GoldenLabel).values(pdf_url=pdf_url, themes=themes)
    session.execute(
        stmt.on_conflict_do_update(
            index_elements=["pdf_url"],
            set_={"themes": stmt.excluded.themes, "labelled_at": func.now()},
        )
    )


def label_count(session: Session) -> int:
    return session.execute(select(func.count()).select_from(GoldenLabel)).scalar_one()
