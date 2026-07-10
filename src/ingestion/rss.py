"""Fetch and parse the Diário da República daily RSS feeds.

The feeds at ``files.diariodarepublica.pt/rss/serie{1,2}.xml`` hold the CURRENT day's issue
only (verified 2026-07-10): one ``<item>`` per act with the act title, the official summary
in ``<description>`` (prefixed with the issuing body, no separator), and a direct PDF link.
Parsing here is strictly deterministic — anything that needs judgement (theme, issuing-body
splitting, plain-language summary) belongs to the LLM pipeline, not the parser.
"""

from __future__ import annotations

import datetime as dt
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import httpx

SERIE1_URL = "https://files.diariodarepublica.pt/rss/serie1.xml"
SERIE2_URL = "https://files.diariodarepublica.pt/rss/serie2.xml"

# "Decreto-Lei n.º 136/2026  -  Diário da República n.º 132/2026, Série I de 2026-07-10"
# Supplements (published later the same day, observed live on day one) insert a segment:
# "... n.º 132/2026, Suplemento, Série I de 2026-07-10" (also "2.º Suplemento", etc.).
_TITLE_RE = re.compile(
    r"^(?P<act>.+?)\s+-\s+Diário da República n\.º\s*(?P<issue>\S+?),"
    r"(?:\s*(?P<supplement>[^,]+),)?"
    r"\s*Série (?P<series>[IV]+) de (?P<date>\d{4}-\d{2}-\d{2})$"
)


class RssParseError(Exception):
    """The feed did not match the format this parser was built against."""


@dataclass(frozen=True)
class GazetteItem:
    """One act as announced in the daily feed (raw, deterministic fields only)."""

    act_title: str  # e.g. "Decreto-Lei n.º 136/2026"
    issue_number: str  # e.g. "132/2026"
    series: str  # "I" | "II"
    supplement: str | None  # e.g. "Suplemento" — published later in the day
    pub_date: dt.date
    summary_raw: str  # issuing body + official summary, as published (no separator)
    pdf_url: str


def parse_feed(xml_text: str) -> list[GazetteItem]:
    """Parse a DR daily feed into items. Raises RssParseError on unexpected shapes."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise RssParseError(f"feed is not valid XML: {exc}") from exc

    channel = root.find("channel")
    if channel is None:
        raise RssParseError("feed has no <channel>")

    items: list[GazetteItem] = []
    for node in channel.findall("item"):
        title = (node.findtext("title") or "").strip()
        match = _TITLE_RE.match(title)
        if not match:
            raise RssParseError(f"item title does not match the known format: {title!r}")

        link = (node.findtext("link") or "").strip()
        if not link.lower().endswith(".pdf"):
            raise RssParseError(f"item link is not a PDF: {link!r}")

        summary = " ".join((node.findtext("description") or "").split())
        items.append(
            GazetteItem(
                act_title=match["act"].strip(),
                issue_number=match["issue"],
                series=match["series"],
                supplement=match["supplement"],
                pub_date=dt.date.fromisoformat(match["date"]),
                summary_raw=summary,
                pdf_url=link,
            )
        )
    return items


def fetch_feed(url: str = SERIE1_URL, client: httpx.Client | None = None) -> str:
    """Download a feed body. The caller decides what to do with days that have no items."""
    owns = client is None
    client = client or httpx.Client(timeout=30)
    try:
        response = client.get(url)
        response.raise_for_status()
        return response.text
    finally:
        if owns:
            client.close()
