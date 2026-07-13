"""Plain-language headline + summary of one act (European Portuguese, facts only).

Same contract discipline as classify: the provider returns raw JSON, pydantic validates it
here. The headline exists because the official act designation ("Portaria n.º 295/2026/1")
carries zero information for a lay reader — each digest entry must work like a newspaper
front page: the headline says WHAT changes for WHOM; the official designation is metadata.
The deterministic number-grounding check in ``verify.py`` covers headline and summary alike.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from src.pipeline.budget import RequestBudget
from src.pipeline.providers import LlmProvider

# How much of the act's text feeds the prompt. Acts are usually short; this cap keeps the
# request well inside flash-lite context and the free-tier token budget.
TEXT_CHARS = 4000

SUMMARIZE_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {"headline": {"type": "STRING"}, "summary": {"type": "STRING"}},
    "required": ["headline", "summary"],
}


class Summary(BaseModel):
    # The prompt asks for <=90 chars; the hard cap only rejects clearly broken outputs
    # (a paragraph masquerading as a headline), not a headline a few chars over.
    headline: str = Field(min_length=10, max_length=140)
    summary: str = Field(min_length=20)


class SummaryError(RuntimeError):
    """The provider's output did not satisfy the summary contract."""


def summarize_prompt(act_title: str, summary_raw: str, act_text: str) -> str:
    return (
        "Rewrite the following act from Portugal's official gazette for a general audience.\n"
        "Produce TWO fields:\n"
        "1. headline — a newspaper-style headline in European Portuguese:\n"
        "   - one line, at most 90 characters, no final period;\n"
        "   - plain language: say WHAT changes and for WHOM;\n"
        "   - NEVER use the act's official designation (type/number) as the headline;\n"
        "   - sober and factual: no sensationalism, no opinions, no wordplay.\n"
        "2. summary — 2 to 3 sentences in European Portuguese, plain language (no legalese):\n"
        "   - ONLY facts present in the source below. No opinions, no additions, no guesses.\n"
        "   - Do not open by restating the act's official designation; lead with the substance.\n"
        "   - Numbers, dates and amounts must be copied exactly from the source.\n\n"
        f"Act title: {act_title}\n"
        f"Official summary: {summary_raw}\n"
        f"Act text (excerpt): {act_text[:TEXT_CHARS]}\n\n"
        'Respond ONLY with JSON: {"headline": "<headline>", "summary": "<2-3 sentences>"}'
    )


def summarize_act(
    provider: LlmProvider,
    budget: RequestBudget,
    act_title: str,
    summary_raw: str,
    act_text: str,
) -> Summary:
    budget.spend()
    raw = provider.complete_json(
        summarize_prompt(act_title, summary_raw, act_text), SUMMARIZE_SCHEMA
    )
    try:
        return Summary.model_validate_json(raw)
    except ValidationError as exc:
        raise SummaryError(f"invalid summary payload: {exc}") from exc
