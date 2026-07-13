"""Blind labelling CLI for the golden set — the author's tool, run locally.

BLIND by design: the tool shows the official title, the official summary and the PDF link,
NEVER the model's classification — a golden set that has seen the model's answers inherits
the model's mistakes and turns "accuracy vs golden set" into a circle (charter principle 2).

Themes are entered as letters, first = primary: "e" → economia; "he" → habitação (primary)
+ economia. The label is written immediately; quitting and resuming later is free because
the queue is derived from what is missing.

Usage:
    uv run --env-file .env python -m src.evals.label
"""

from __future__ import annotations

import textwrap

from src.db.engine import make_engine, make_session_factory
from src.db.repositories.golden import acts_missing_label, label_count, upsert_label

THEME_KEYS = {"h": "habitacao", "s": "saude", "e": "economia", "o": "outros"}
GOAL = 100  # target size of the golden set (charter)
EXCERPT_CHARS = 700


def parse_themes(raw: str) -> list[str] | None:
    """'he' → ['habitacao', 'economia'] (order = priority). None if any key is invalid,
    a key repeats, or the input is empty — the caller re-prompts."""
    keys = list(raw.strip().lower())
    if not keys or len(set(keys)) != len(keys):
        return None
    themes = [THEME_KEYS[k] for k in keys if k in THEME_KEYS]
    return themes if len(themes) == len(keys) else None


def main() -> None:
    engine = make_engine()
    factory = make_session_factory(engine)
    try:
        with factory() as session:
            queue = acts_missing_label(session)
            done = label_count(session)
        if not queue:
            print(f"Nada por etiquetar — golden set com {done}/{GOAL}.")
            return
        print(
            f"Golden set: {done}/{GOAL} etiquetados, {len(queue)} por etiquetar.\n"
            "Temas: [h]abitação [s]aúde [e]conomia [o]utros — 1ª letra = tema principal.\n"
            "Comandos: t = ver excerto do texto, k = saltar, q = sair.\n"
        )
        for pdf_url, act_title, summary_raw, text, pub_date in queue:
            print(f"─── {pub_date} · {act_title}")
            print(textwrap.fill(summary_raw, width=98, initial_indent="  ", subsequent_indent="  "))
            print(f"  {pdf_url}")
            while True:
                raw = input("temas> ").strip().lower()
                if raw == "q":
                    print(f"Sessão terminada — golden set com {done}/{GOAL}.")
                    return
                if raw == "k":
                    break
                if raw == "t":
                    excerpt = " ".join(text.split())[:EXCERPT_CHARS]
                    print(textwrap.fill(excerpt, width=98, initial_indent="  │ ",
                                        subsequent_indent="  │ "))  # fmt: skip
                    continue
                themes = parse_themes(raw)
                if themes is None:
                    print("  entrada inválida — letras de {h,s,e,o}, sem repetir (ex.: e, he)")
                    continue
                with factory() as session:
                    upsert_label(session, pdf_url=pdf_url, themes=themes)
                    session.commit()
                done += 1
                print(f"  ✓ {', '.join(themes)}   [{done}/{GOAL}]\n")
                break
        print(f"Fila esgotada — golden set com {done}/{GOAL}.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
