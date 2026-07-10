"""Deterministic grounding checks — the free guardrail between the LLM and publication.

LLM-as-judge costs requests and inherits the judge's blind spots. Numbers don't: every
number in a summary must literally exist in the source, or the summary is flagged. This
catches the classic hallucination mode of legal summarisation (invented amounts, dates,
article numbers) at zero cost, with zero false trust.
"""

from __future__ import annotations

import re

# Numeric tokens: integers, decimals with . or , and digit groups ("1 500 000" → parts).
_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")


def _normalise(token: str) -> str:
    """Comparable form of a numeric token: decimal comma → dot, trailing '.0' stripped."""
    token = token.replace(",", ".")
    if "." in token:
        token = token.rstrip("0").rstrip(".")
    return token


def numbers_in(text: str) -> set[str]:
    return {_normalise(m) for m in _NUMBER_RE.findall(text)}


def ungrounded_numbers(summary: str, source: str) -> list[str]:
    """Numbers present in the summary but absent from the source (empty list = grounded)."""
    missing = numbers_in(summary) - numbers_in(source)
    return sorted(missing)
