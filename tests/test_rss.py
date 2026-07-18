"""RSS parser tests against a real captured feed (2026-07-10, Série I, 7 acts)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from src.ingestion.rss import GazetteItem, RssParseError, parse_feed

FIXTURE = Path(__file__).parent / "fixtures" / "serie1-2026-07-10.xml"


def _items() -> list[GazetteItem]:
    return parse_feed(FIXTURE.read_text(encoding="utf-8"))


def test_parses_all_items_of_the_day() -> None:
    items = _items()
    assert len(items) == 8  # 7 morning acts + 1 supplement published during the day
    assert all(i.series == "I" for i in items)
    assert all(i.pub_date == dt.date(2026, 7, 10) for i in items)
    assert all(i.issue_number == "132/2026" for i in items)


def test_supplement_variant_is_parsed() -> None:
    # Supplements insert an extra title segment — a real day-one catch, kept as regression.
    supp = [i for i in _items() if i.supplement is not None]
    assert len(supp) == 1
    assert supp[0].act_title == "Portaria n.º 294-A/2026/1"
    assert supp[0].supplement == "Suplemento"
    assert [i.supplement for i in _items()[:7]] == [None] * 7


def test_first_item_fields() -> None:
    first = _items()[0]
    assert first.act_title == "Decreto-Lei n.º 136/2026"
    assert first.pdf_url.startswith("https://files.diariodarepublica.pt/1s/2026/07/")
    assert first.pdf_url.endswith(".pdf")
    # summary_raw = issuing body + official summary, whitespace-normalised
    assert first.summary_raw.startswith("Presidência do Conselho de Ministros")
    assert "Fundo Europeu" in first.summary_raw
    assert "\n" not in first.summary_raw


def test_non_pdf_link_is_quarantined_not_fatal(caplog: pytest.LogCaptureFixture) -> None:
    # INCM emits image-link items (annex images; first seen in Série I on 2026-07-16,
    # where one aborted ingestion for three days). They are skipped loudly, never fatal.
    xml = (
        '<?xml version="1.0"?><rss version="2.0"><channel>'
        "<item><title>Decreto-Lei n.º 146/2026  -  Diário da República n.º 137/2026, "
        "Série I de 2026-07-17</title><description>d</description>"
        "<link>https://files.diariodarepublica.pt/xternal/images/x.jpg</link></item>"
        "<item><title>Portaria n.º 1/2026  -  Diário da República n.º 137/2026, "
        "Série I de 2026-07-17</title><description>d</description>"
        "<link>https://files.diariodarepublica.pt/1s/2026/07/13700/0000100002.pdf</link></item>"
        "</channel></rss>"
    )
    with caplog.at_level("WARNING", logger="rss"):
        items = parse_feed(xml)
    assert [i.act_title for i in items] == ["Portaria n.º 1/2026"]
    assert any("Decreto-Lei n.º 146/2026" in r.getMessage() for r in caplog.records)


def test_empty_channel_yields_no_items() -> None:
    xml = '<?xml version="1.0"?><rss version="2.0"><channel><title>t</title></channel></rss>'
    assert parse_feed(xml) == []


def test_unknown_title_format_raises() -> None:
    xml = (
        '<?xml version="1.0"?><rss version="2.0"><channel>'
        "<item><title>Algo inesperado</title><link>x.pdf</link></item>"
        "</channel></rss>"
    )
    with pytest.raises(RssParseError, match="known format"):
        parse_feed(xml)


def test_invalid_xml_raises() -> None:
    with pytest.raises(RssParseError, match="not valid XML"):
        parse_feed("isto não é XML")
