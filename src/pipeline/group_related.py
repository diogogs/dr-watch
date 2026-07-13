"""Group a day's acts into subject clusters — one LLM request per day, presentation-only.

Same-day acts often come in packs (two AR resolutions on the same policy, an act and its
correction); one card per act makes the same story read as separate news. Grouping fixes
the PRESENTATION without merging content: each act keeps its own headline, summary and
citation — the LLM only says which acts share a subject. A deterministic validator rejects
any output that references unknown acts or uses an act twice, and a rejected (or absent)
grouping falls back to ungrouped display: grouping can never break a digest.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from src.pipeline.budget import RequestBudget
from src.pipeline.providers import LlmProvider

GROUP_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "groups": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "label": {"type": "STRING"},
                    "member_ids": {"type": "ARRAY", "items": {"type": "INTEGER"}},
                },
                "required": ["label", "member_ids"],
            },
        }
    },
    "required": ["groups"],
}


class Group(BaseModel):
    label: str = Field(min_length=3)
    member_ids: list[int] = Field(min_length=2)  # a "group" of one is not a group


class Grouping(BaseModel):
    groups: list[Group]


class GroupingError(RuntimeError):
    """The provider's output did not satisfy the grouping contract."""


def group_prompt(acts: list[tuple[str, str]]) -> str:
    """``acts`` is (official title, headline) in display order; ids are 1-based."""
    lines = "\n".join(f"[{i}] {title} — {headline}" for i, (title, headline) in enumerate(acts, 1))
    return (
        "You will see the acts published in one day of Portugal's official gazette.\n"
        "Group ONLY acts that are clearly about the same specific subject (e.g., two "
        "resolutions on the same policy, an act and its correction). Acts on different "
        "subjects within the same broad area are NOT a group. When in doubt, do NOT group.\n\n"
        f"{lines}\n\n"
        "Respond ONLY with JSON listing groups of 2 or more acts (empty list if none):\n"
        '{"groups": [{"label": "<short subject, in Portuguese>", "member_ids": [1, 2]}]}'
    )


def validate_groups(groups: list[Group], n_acts: int) -> None:
    """Every referenced id must exist and no act may appear in two groups."""
    seen: set[int] = set()
    for group in groups:
        for member_id in group.member_ids:
            if member_id < 1 or member_id > n_acts:
                raise GroupingError(f"unknown act id {member_id} (day has {n_acts} acts)")
            if member_id in seen:
                raise GroupingError(f"act id {member_id} assigned to more than one group")
            seen.add(member_id)


def group_acts(
    provider: LlmProvider, budget: RequestBudget, acts: list[tuple[str, str]]
) -> list[Group]:
    """One grouping request for one day. Callers treat GroupingError as 'publish ungrouped'."""
    budget.spend()
    raw = provider.complete_json(group_prompt(acts), GROUP_SCHEMA)
    try:
        grouping = Grouping.model_validate_json(raw)
    except ValidationError as exc:
        raise GroupingError(f"invalid grouping payload: {exc}") from exc
    validate_groups(grouping.groups, len(acts))
    return grouping.groups
