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
    headline: str | None  # None on v0 rows only; display falls back to act_title
    summary_plain: str
    pdf_url: str
    flagged: bool  # ungrounded numbers present → shown with a warning, or held back


# Normative weight of an act, from its official designation. Within a theme, acts that
# change the law outrank recommendations, which outrank typo corrections — the digest reads
# like a front page: most consequential first. Deterministic (title prefix), no LLM.
# Mirrored in web/lib/db.ts (actRank) — keep the two in sync.
_ACT_RANK: tuple[tuple[str, int], ...] = (
    ("lei orgânica", 0),
    ("lei ", 0),
    ("decreto-lei", 0),
    ("decreto legislativo regional", 0),
    ("decreto do presidente", 1),
    ("decreto regulamentar", 1),
    ("portaria", 1),
    ("resolução do conselho de ministros", 2),
    ("acórdão", 2),
    ("resolução", 3),
    ("declaração de retificação", 5),
)


def act_rank(act_title: str) -> int:
    title = act_title.casefold()
    for prefix, rank in _ACT_RANK:
        if title.startswith(prefix):
            return rank
    return 4  # unknown designations sort after known ones, before retifications


def daily_digest(
    session: Session, pub_date: dt.date, prompt_version: str = PROMPT_VERSION
) -> list[DigestEntry]:
    """A day's analysed acts: primary theme (habitação → saúde → economia → outros), then
    normative weight within the theme."""
    stmt = (
        select(
            GazetteItem.act_title,
            ActAnalysis.themes,
            ActAnalysis.headline,
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
            headline=headline,
            summary_plain=summary,
            pdf_url=url,
            flagged=bool(ungrounded),
        )
        for title, themes, headline, summary, url, ungrounded in session.execute(stmt).all()
    ]
    return sorted(
        entries,
        key=lambda e: (THEME_ORDER.index(e.themes[0]), act_rank(e.act_title), e.act_title),
    )


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
                print(f"\n{e.headline or e.act_title}{flag}")
                print(f"  [{e.act_title}]")
                print(f"  {e.summary_plain}")
                print(f"  → {e.pdf_url}")
            print()
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
