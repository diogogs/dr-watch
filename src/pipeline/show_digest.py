"""Compose and print a day's digest — the site's query, exercised from the terminal.

The digest is DERIVED, not stored: act_analysis is insert-only and versioned, so the digest
for a date at a prompt version is deterministic. This module owns that composition query so
the future site and any test hit exactly the same logic.

Usage:
    uv run --env-file .env python -m src.pipeline.show_digest [YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import datetime as dt
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.engine import make_engine, make_session_factory
from src.db.models import ActAnalysis, GazetteItem
from src.pipeline.run_analysis import PROMPT_VERSION

THEME_ORDER = ("habitacao", "saude", "economia", "outros")
THEME_LABEL = {
    "habitacao": "Habitação",
    "saude": "Saúde",
    "economia": "Economia",
    "outros": "Outros",
}


@dataclass(frozen=True)
class DigestEntry:
    act_title: str
    themes: tuple[str, ...]
    summary_plain: str
    pdf_url: str
    flagged: bool  # ungrounded numbers present → shown with a warning, or held back


def daily_digest(
    session: Session, pub_date: dt.date, prompt_version: str = PROMPT_VERSION
) -> list[DigestEntry]:
    """A day's analysed acts, primary-theme ordered (habitação → saúde → economia → outros)."""
    stmt = (
        select(
            GazetteItem.act_title,
            ActAnalysis.themes,
            ActAnalysis.summary_plain,
            GazetteItem.pdf_url,
            ActAnalysis.ungrounded_numbers,
        )
        .join(ActAnalysis, ActAnalysis.pdf_url == GazetteItem.pdf_url)
        .where(GazetteItem.pub_date == pub_date, ActAnalysis.prompt_version == prompt_version)
    )
    entries = [
        DigestEntry(
            act_title=title,
            themes=tuple(themes),
            summary_plain=summary,
            pdf_url=url,
            flagged=bool(ungrounded),
        )
        for title, themes, summary, url, ungrounded in session.execute(stmt).all()
    ]
    return sorted(entries, key=lambda e: (THEME_ORDER.index(e.themes[0]), e.act_title))


def main() -> None:
    parser = argparse.ArgumentParser(description="Print a day's digest.")
    parser.add_argument(
        "date",
        nargs="?",
        type=dt.date.fromisoformat,
        default=dt.datetime.now(tz=dt.UTC).date(),
    )
    args = parser.parse_args()

    engine = make_engine()
    try:
        with make_session_factory(engine)() as session:
            entries = daily_digest(session, args.date)
        print(f"Diário da República — Série I, {args.date} ({len(entries)} diplomas)\n")
        for theme in THEME_ORDER:
            themed = [e for e in entries if e.themes[0] == theme]
            if not themed:
                continue
            print(f"── {THEME_LABEL[theme]} " + "─" * (60 - len(THEME_LABEL[theme])))
            for e in themed:
                flag = "  [!] números por verificar" if e.flagged else ""
                print(f"\n{e.act_title}{flag}")
                print(f"  {e.summary_plain}")
                print(f"  → {e.pdf_url}")
            print()
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
