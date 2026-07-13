"""Analyse every act that has text but no analysis: classify + summarize + verify → persist.

Two LLM requests per act, spent against a per-run budget BEFORE each call. Budget exhaustion
is an HONEST PARTIAL result (logged, exit 0 — the next run continues where this one stopped,
because the work queue is derived from what is missing). Per-act failures are isolated and
surface through the exit code.

After the per-act work, one grouping request per affected day clusters same-subject acts
for presentation (see group_related.py). Grouping failures are logged and skipped — a day
without a grouping row simply renders ungrouped.

Usage:
    uv run --env-file .env python -m src.pipeline.run_analysis [--max-requests 100]
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

import httpx
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings
from src.db.engine import make_engine, make_session_factory
from src.db.models import PipelineRun
from src.db.repositories.analysis import (
    acts_for_grouping,
    acts_missing_analysis,
    analysed_days_without_grouping,
    insert_analysis,
    insert_day_grouping,
)
from src.pipeline.budget import BudgetExhausted, RequestBudget
from src.pipeline.classify import classify_act
from src.pipeline.group_related import group_acts
from src.pipeline.providers import LlmProvider, provider_from_settings
from src.pipeline.summarize import summarize_act
from src.pipeline.verify import ungrounded_numbers

logger = logging.getLogger("run_analysis")

PROMPT_VERSION = "v1"  # bumping this deliberately re-analyses history into NEW rows

# Pacing between acts (2 requests each): free tiers limit requests per MINUTE, and bursting
# a whole issue in seconds earns 429s (observed 2026-07-13). ~12s/act ≈ 10 requests/minute.
THROTTLE_SECONDS = 6.0


def check_citations(urls: list[str]) -> tuple[int, int]:
    """(ok, total): does each analysis' official-PDF citation still resolve? The citation IS
    the product's trust anchor, so it gets verified on every run, not assumed."""
    ok = 0
    with httpx.Client(timeout=30) as client:
        for url in urls:
            try:
                if client.head(url, follow_redirects=True).status_code == 200:
                    ok += 1
            except httpx.HTTPError:
                logger.warning("citation did not resolve: %s", url)
    return ok, len(urls)


def group_days(factory: sessionmaker[Session], provider: LlmProvider, budget: RequestBudget) -> int:
    """One grouping request per day still lacking a grouping row; returns days grouped.

    Days whose acts were analysed in THIS run have no row yet, so they are always included —
    and a day that gains late acts in a future run gets a fresh row then (append-only).
    """
    with factory() as session:
        days = analysed_days_without_grouping(session, PROMPT_VERSION)
    grouped = 0
    for day in days:
        with factory() as session:
            acts = acts_for_grouping(session, day, PROMPT_VERSION)
        pdf_urls = [pdf_url for pdf_url, _, _ in acts]
        if len(acts) >= 2:
            if grouped > 0:
                time.sleep(THROTTLE_SECONDS)
            try:
                pairs = [(title, headline or title) for _, title, headline in acts]
                groups = group_acts(provider, budget, pairs)
            except BudgetExhausted:
                logger.warning("budget exhausted — %d days left ungrouped", len(days) - grouped)
                break
            except Exception:  # includes GroupingError — an invalid grouping is never fatal
                logger.exception("grouping failed for %s — day renders ungrouped", day)
                continue
            payload = [
                {"label": g.label, "pdf_urls": [pdf_urls[i - 1] for i in g.member_ids]}
                for g in groups
            ]
            model_name = provider.name
        else:
            payload, model_name = [], "deterministic:single-act-day"
        with factory() as session:
            insert_day_grouping(
                session,
                pub_date=day,
                prompt_version=PROMPT_VERSION,
                groups=payload,
                model_name=model_name,
            )
            session.commit()
        grouped += 1
        logger.info("%s: %d group(s) of related acts", day, len(payload))
    return grouped


def run_analysis(max_requests: int = 100) -> dict[str, int]:
    settings = get_settings()
    provider = provider_from_settings(settings)
    budget = RequestBudget(max_requests)
    engine = make_engine()
    factory = make_session_factory(engine)
    stats = {"queued": 0, "analysed": 0, "flagged": 0, "failed": 0, "deferred": 0}
    analysed_urls: list[str] = []

    try:
        with factory() as session:
            queue = acts_missing_analysis(session, PROMPT_VERSION)
        stats["queued"] = len(queue)
        logger.info("provider=%s queue=%d budget=%d", provider.name, len(queue), max_requests)

        for i, (pdf_url, act_title, summary_raw, text, _pub_date) in enumerate(queue):
            if i > 0:
                time.sleep(THROTTLE_SECONDS)
            try:
                classification = classify_act(provider, budget, act_title, summary_raw)
                summary = summarize_act(provider, budget, act_title, summary_raw, text)
            except BudgetExhausted:
                stats["deferred"] = stats["queued"] - stats["analysed"] - stats["failed"]
                logger.warning("budget exhausted — %d acts deferred to next run", stats["deferred"])
                break
            except Exception:
                stats["failed"] += 1
                logger.exception("analysis failed: %s", act_title)
                continue

            source = f"{act_title}\n{summary_raw}\n{text}"
            ungrounded = ungrounded_numbers(f"{summary.headline}\n{summary.summary}", source)
            if ungrounded:
                stats["flagged"] += 1
                logger.warning("%s: ungrounded numbers %s — flagged", act_title, ungrounded)

            with factory() as session:
                insert_analysis(
                    session,
                    pdf_url=pdf_url,
                    prompt_version=PROMPT_VERSION,
                    themes=list(classification.themes),
                    rationale=classification.rationale,
                    headline=summary.headline,
                    summary_plain=summary.summary,
                    ungrounded=ungrounded,
                    model_name=provider.name,
                )
                session.commit()
            stats["analysed"] += 1
            analysed_urls.append(pdf_url)
            logger.info("%s -> %s", act_title, ",".join(classification.themes))

        # Presentation grouping: one request per day that lacks a grouping row. Runs even
        # when the analyse queue was empty (self-heals days whose grouping failed before).
        try:
            group_days(factory, provider, budget)
        except Exception:
            logger.exception("grouping phase failed — affected days render ungrouped")

        # Evals: citation check for this run's analyses + the append-only run record.
        citation_ok, citation_total = check_citations(analysed_urls)
        with factory() as session:
            session.add(
                PipelineRun(
                    prompt_version=PROMPT_VERSION,
                    queued=stats["queued"],
                    analysed=stats["analysed"],
                    flagged=stats["flagged"],
                    failed=stats["failed"],
                    deferred=stats["deferred"],
                    citation_ok=citation_ok,
                    citation_total=citation_total,
                    model_name=provider.name,
                )
            )
            session.commit()
        logger.info("citations: %d/%d ok", citation_ok, citation_total)
    finally:
        engine.dispose()

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify + summarise acts missing analysis.")
    parser.add_argument("--max-requests", type=int, default=100)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stats = run_analysis(args.max_requests)
    logger.info("done: %s", stats)
    if stats["failed"]:
        sys.exit(1)  # hard failures surface; budget deferral does not


if __name__ == "__main__":
    main()
