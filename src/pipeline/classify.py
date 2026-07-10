"""Theme classification of gazette acts (v1 themes: habitação, saúde, economia, outros).

The provider returns raw JSON; THIS module owns the contract via pydantic validation, so a
provider swap (or a provider hallucinating a theme) can never leak an invalid label into the
system. Prompt wording stays deliberately v0 until the golden set exists — tuning against
vibes instead of labels is what charter principle 2 forbids.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from src.pipeline.budget import RequestBudget
from src.pipeline.providers import LlmProvider

Theme = Literal["habitacao", "saude", "economia", "outros"]

# Gemini responseSchema (OpenAPI subset, uppercase types). Groq ignores it; pydantic rules.
CLASSIFY_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "themes": {
            "type": "ARRAY",
            "items": {
                "type": "STRING",
                "enum": ["habitacao", "saude", "economia", "outros"],
            },
        },
        "rationale": {"type": "STRING"},
    },
    "required": ["themes", "rationale"],
}


class Classification(BaseModel):
    themes: list[Theme] = Field(min_length=1)
    rationale: str


class ClassificationError(RuntimeError):
    """The provider's output did not satisfy the classification contract."""


def classify_prompt(act_title: str, summary_raw: str) -> str:
    return (
        "You classify acts from Portugal's official gazette (Diário da República) into "
        "themes.\n\n"
        "Themes — choose every one that clearly applies; if none applies, answer exactly "
        '["outros"]:\n'
        "- habitacao: housing — arrendamento, habitação pública ou acessível, construção e "
        "licenciamento habitacional, apoios à habitação, alojamento local.\n"
        "- saude: health — SNS, hospitais e cuidados de saúde, medicamentos e farmácias, "
        "saúde pública, carreiras e contratação na saúde.\n"
        "- economia: economy — impostos e fiscalidade, empresas e investimento, trabalho e "
        "salários, apoios e incentivos económicos, finanças públicas, comércio.\n\n"
        f"Act title: {act_title}\n"
        f"Official summary: {summary_raw}\n\n"
        'Respond ONLY with JSON: {"themes": [...], "rationale": "<one sentence, in '
        'Portuguese>"}'
    )


def classify_act(
    provider: LlmProvider, budget: RequestBudget, act_title: str, summary_raw: str
) -> Classification:
    """One classification request. Budget is spent BEFORE the call (never overruns the tier)."""
    budget.spend()
    raw = provider.complete_json(classify_prompt(act_title, summary_raw), CLASSIFY_SCHEMA)
    try:
        return Classification.model_validate_json(raw)
    except ValidationError as exc:
        raise ClassificationError(f"invalid classification payload: {exc}") from exc
