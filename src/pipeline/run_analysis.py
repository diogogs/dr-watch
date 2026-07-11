"""Analyse every act that has text but no analysis: classify + summarize + verify → persist.

Two LLM requests per act, spent against a per-run budget BEFORE each call. Budget exhaustion
is an HONEST PARTIAL result (logged, exit 0 — the next run continues where this one stopped,
because the work queue is derived from what is missing). Per-act failures are isolated and
surface through the exit code.

Usage:
    uv run --env-file .env python -m src.pipeline.run_analysis [--max-requests 100]
"""

from __future__ import annotations

import argparse
import logging
import sys

import httpx

from src.config import get_settings
from src.db.engine import make_engine, make_session_factory
from src.db.models import PipelineRun
from src.db.repositories.analysis import acts_missing_analysis, insert_analysis
from src.pipeline.budget import BudgetExhausted, RequestBudget
from src.pipeline.classify import classify_act
from src.pipeline.providers import provider_from_settings
from src.pipeline.summarize import summarize_act
from src.pipeline.verify import ungrounded_numbers

logger = logging.getLogger("run_analysis")

PROMPT_VERSION = "v0"  # bumping this deliberately re-analyses history into NEW rows


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

        for pdf_url, act_title, summary_raw, text in queue:
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
            ungrounded = ungrounded_numbers(summary.summary, source)
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
                    summary_plain=summary.summary,
                    ungrounded=ungrounded,
                    model_name=provider.name,
                )
                session.commit()
            stats["analysed"] += 1
            analysed_urls.append(pdf_url)
            logger.info("%s -> %s", act_title, ",".join(classification.themes))

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
