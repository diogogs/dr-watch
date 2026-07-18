"""Daily ingestion: today's Série I feed → raw.gazette_item, missing PDFs → raw.act_text.

Idempotent by construction (upsert by pdf_url, first_seen_at never touched, act texts insert-
once), so re-runs heal gaps — including supplements published later the same day. Per-item
isolation on PDF extraction: one bad PDF is counted and logged, never fatal to the run.

Usage:
    uv run --env-file .env python -m src.ingestion.daily [--feed-file data/rss/....xml]

``--feed-file`` ingests a committed snapshot instead of the live feed — the recovery path
when the live feed has moved past a day that failed (the snapshots exist for exactly this).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import httpx

from src.db.engine import make_engine, make_session_factory
from src.db.repositories.gazette import insert_act_text, upsert_gazette_items, urls_missing_text
from src.ingestion.pdf_text import extract_act_text, fetch_pdf
from src.ingestion.rss import SERIE1_URL, fetch_feed, parse_feed

logger = logging.getLogger("daily")


def run_daily(feed_file: Path | None = None) -> dict[str, int]:
    """Ingest today's announcements and any missing act texts. Returns run counters."""
    engine = make_engine()
    factory = make_session_factory(engine)
    stats = {"items_seen": 0, "texts_added": 0, "texts_failed": 0}

    try:
        feed_xml = feed_file.read_text(encoding="utf-8") if feed_file else fetch_feed(SERIE1_URL)
        items = parse_feed(feed_xml)
        stats["items_seen"] = len(items)
        with factory() as session:
            upsert_gazette_items(session, items)
            session.commit()
        logger.info("feed: %d items upserted", len(items))

        with factory() as session:
            missing = urls_missing_text(session)
        logger.info("acts missing text: %d", len(missing))

        with httpx.Client(timeout=60) as client:
            for url in missing:
                # One bad PDF must not kill the run; a re-run heals whatever failed here.
                try:
                    text = extract_act_text(fetch_pdf(url, client))
                    with factory() as session:
                        insert_act_text(session, url, text)
                        session.commit()
                    stats["texts_added"] += 1
                    logger.info("text extracted: %s (%d chars)", url, len(text))
                except Exception:
                    stats["texts_failed"] += 1
                    logger.exception("text extraction failed: %s", url)
    finally:
        engine.dispose()

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest the Série I feed (live or snapshot).")
    parser.add_argument("--feed-file", type=Path, default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stats = run_daily(args.feed_file)
    logger.info("done: %s", stats)
    if stats["texts_failed"]:
        sys.exit(1)  # honest failure: the cron must surface partial extraction


if __name__ == "__main__":
    main()
