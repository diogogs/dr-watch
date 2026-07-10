"""Pipeline plumbing tests: budget guard, fallback chain, classification contract."""

from __future__ import annotations

from typing import Any

import pytest

from src.pipeline.budget import BudgetExhausted, RequestBudget
from src.pipeline.classify import Classification, ClassificationError, classify_act
from src.pipeline.providers import FallbackChain, ProviderError


class FakeProvider:
    def __init__(self, payload: str, fail: bool = False, name: str = "fake") -> None:
        self.payload = payload
        self.fail = fail
        self.name = name
        self.calls = 0

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> str:
        self.calls += 1
        if self.fail:
            raise ProviderError(f"{self.name}: down")
        return self.payload


GOOD = '{"themes": ["habitacao", "economia"], "rationale": "Apoios ao arrendamento."}'


def test_classify_parses_valid_payload() -> None:
    result = classify_act(FakeProvider(GOOD), RequestBudget(10), "Decreto-Lei X", "sumário")
    assert result == Classification(
        themes=["habitacao", "economia"], rationale="Apoios ao arrendamento."
    )


def test_classify_rejects_unknown_theme() -> None:
    bad = '{"themes": ["desporto"], "rationale": "..."}'
    with pytest.raises(ClassificationError):
        classify_act(FakeProvider(bad), RequestBudget(10), "t", "s")


def test_classify_rejects_empty_themes_and_non_json() -> None:
    with pytest.raises(ClassificationError):
        classify_act(FakeProvider('{"themes": [], "rationale": "x"}'), RequestBudget(10), "t", "s")
    with pytest.raises(ClassificationError):
        classify_act(FakeProvider("not json at all"), RequestBudget(10), "t", "s")


def test_budget_spends_before_the_call_and_exhausts() -> None:
    provider = FakeProvider(GOOD)
    budget = RequestBudget(2)
    classify_act(provider, budget, "t", "s")
    classify_act(provider, budget, "t", "s")
    with pytest.raises(BudgetExhausted):
        classify_act(provider, budget, "t", "s")
    assert provider.calls == 2  # the third call never reached the provider
    assert budget.remaining == 0


def test_fallback_chain_uses_second_when_first_fails() -> None:
    primary = FakeProvider("", fail=True, name="primary")
    secondary = FakeProvider(GOOD, name="secondary")
    chain = FallbackChain([primary, secondary])
    assert chain.complete_json("p", {}) == GOOD
    assert primary.calls == 1 and secondary.calls == 1


def test_fallback_chain_reports_all_failures() -> None:
    chain = FallbackChain(
        [FakeProvider("", fail=True, name="a"), FakeProvider("", fail=True, name="b")]
    )
    with pytest.raises(ProviderError, match=r"a: down.*b: down"):
        chain.complete_json("p", {})
