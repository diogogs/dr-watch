"""Golden-set tests: blind-input parsing (unit) and the label repository (integration)."""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.db.models import ActText, GazetteItem, GoldenLabel
from src.db.repositories.gazette import insert_act_text, upsert_gazette_items
from src.db.repositories.golden import acts_missing_label, upsert_label
from src.evals.label import parse_themes
from src.ingestion.rss import GazetteItem as FeedItem


def test_parse_themes_order_is_priority() -> None:
    assert parse_themes("e") == ["economia"]
    assert parse_themes("he") == ["habitacao", "economia"]
    assert parse_themes(" SO ") == ["saude", "outros"]


def test_parse_themes_rejects_bad_input() -> None:
    assert parse_themes("") is None
    assert parse_themes("x") is None
    assert parse_themes("hh") is None  # repeated key
    assert parse_themes("hx") is None  # any invalid key rejects the whole input


_URL = "https://files.test.invalid/1s/2099/01/00100/0000300004.pdf"


@pytest.mark.integration
def test_label_queue_and_overwrite(pg_session: Session) -> None:
    item = FeedItem(
        act_title="Portaria n.º 2/2099",
        issue_number="1/2099",
        series="I",
        supplement=None,
        pub_date=dt.date(2099, 1, 2),
        summary_raw="Entidade Teste Sumário.",
        pdf_url=_URL,
    )
    try:
        upsert_gazette_items(pg_session, [item])
        insert_act_text(pg_session, _URL, "texto do diploma")
        pg_session.commit()
        assert _URL in [row[0] for row in acts_missing_label(pg_session)]

        upsert_label(pg_session, pdf_url=_URL, themes=["economia"])
        pg_session.commit()
        assert _URL not in [row[0] for row in acts_missing_label(pg_session)]

        # Re-labelling a mistake overwrites — the golden set is eval input, not history.
        upsert_label(pg_session, pdf_url=_URL, themes=["habitacao", "economia"])
        pg_session.commit()
        stored = pg_session.execute(
            select(GoldenLabel.themes).where(GoldenLabel.pdf_url == _URL)
        ).scalar_one()
        assert stored == ["habitacao", "economia"]
    finally:
        pg_session.rollback()
        pg_session.execute(delete(GoldenLabel).where(GoldenLabel.pdf_url == _URL))
        pg_session.execute(delete(ActText).where(ActText.pdf_url == _URL))
        pg_session.execute(delete(GazetteItem).where(GazetteItem.pdf_url == _URL))
        pg_session.commit()
