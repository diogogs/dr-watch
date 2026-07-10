"""Integration tests for the raw-layer repository: idempotence and the text workflow.

Sentinel rows use an invalid host in the pdf_url (never collides with real data) and are
cleaned up in try/finally, so running against the live database is safe.
"""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.db.models import ActText, GazetteItem
from src.db.repositories.gazette import insert_act_text, upsert_gazette_items, urls_missing_text
from src.ingestion.rss import GazetteItem as FeedItem

pytestmark = pytest.mark.integration

_URL = "https://files.test.invalid/1s/2099/01/00100/0000100002.pdf"


def _feed_item(summary: str = "Entidade Teste Sumário original.") -> FeedItem:
    return FeedItem(
        act_title="Decreto-Lei n.º 1/2099",
        issue_number="1/2099",
        series="I",
        supplement=None,
        pub_date=dt.date(2099, 1, 2),
        summary_raw=summary,
        pdf_url=_URL,
    )


def _cleanup(session: Session) -> None:
    session.rollback()
    session.execute(delete(ActText).where(ActText.pdf_url == _URL))
    session.execute(delete(GazetteItem).where(GazetteItem.pdf_url == _URL))
    session.commit()


def test_upsert_keeps_first_seen_and_refreshes_fields(pg_session: Session) -> None:
    try:
        upsert_gazette_items(pg_session, [_feed_item()])
        pg_session.commit()
        row = pg_session.get(GazetteItem, _URL)
        assert row is not None
        first_seen = row.first_seen_at

        upsert_gazette_items(pg_session, [_feed_item(summary="Entidade Teste Sumário CORRIGIDO.")])
        pg_session.commit()
        pg_session.expire_all()
        row = pg_session.get(GazetteItem, _URL)
        assert row is not None
        assert row.first_seen_at == first_seen  # publication anchor never moves
        assert row.last_seen_at >= first_seen
        assert "CORRIGIDO" in row.summary_raw  # announced fields refresh within the day
    finally:
        _cleanup(pg_session)


def test_text_workflow_and_immutability(pg_session: Session) -> None:
    try:
        upsert_gazette_items(pg_session, [_feed_item()])
        pg_session.commit()
        assert _URL in urls_missing_text(pg_session)

        insert_act_text(pg_session, _URL, "texto original do diploma")
        pg_session.commit()
        assert _URL not in urls_missing_text(pg_session)

        # The official PDF is immutable — a second insert must be a no-op, not an overwrite.
        insert_act_text(pg_session, _URL, "texto adulterado")
        pg_session.commit()
        stored = pg_session.execute(
            select(ActText.text).where(ActText.pdf_url == _URL)
        ).scalar_one()
        assert stored == "texto original do diploma"
    finally:
        _cleanup(pg_session)
