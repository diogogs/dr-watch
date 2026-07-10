"""Plain-language summary of one act (European Portuguese, 2-3 sentences, facts only).

Same contract discipline as classify: the provider returns raw JSON, pydantic validates it
here. The prompt stays v0 until the golden set exists; the deterministic number-grounding
check in ``verify.py`` is what stands between this step and publication.
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
    "properties": {"summary": {"type": "STRING"}},
    "required": ["summary"],
}


class Summary(BaseModel):
    summary: str = Field(min_length=20)


class SummaryError(RuntimeError):
    """The provider's output did not satisfy the summary contract."""


def summarize_prompt(act_title: str, summary_raw: str, act_text: str) -> str:
    return (
        "Rewrite the following act from Portugal's official gazette for a general audience.\n"
        "Rules:\n"
        "- European Portuguese, 2 to 3 sentences, plain language (no legalese).\n"
        "- ONLY facts present in the source below. No opinions, no additions, no guesses.\n"
        "- Numbers, dates and amounts must be copied exactly from the source.\n\n"
        f"Act title: {act_title}\n"
        f"Official summary: {summary_raw}\n"
        f"Act text (excerpt): {act_text[:TEXT_CHARS]}\n\n"
        'Respond ONLY with JSON: {"summary": "<2-3 sentences in Portuguese>"}'
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
