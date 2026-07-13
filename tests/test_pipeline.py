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


def test_summarize_parses_headline_and_summary() -> None:
    from src.pipeline.summarize import summarize_act

    good = (
        '{"headline": "Famílias passam a ter apoio à renda",'
        ' "summary": "O diploma cria um apoio à renda para famílias elegíveis."}'
    )
    result = summarize_act(FakeProvider(good), RequestBudget(10), "t", "s", "texto")
    assert result.headline == "Famílias passam a ter apoio à renda"
    assert "apoio" in result.summary


def test_summarize_rejects_broken_contracts() -> None:
    from src.pipeline.summarize import SummaryError, summarize_act

    headline = '"headline": "Famílias passam a ter apoio à renda"'
    cases = [
        f'{{{headline}, "summary": "curto"}}',  # summary too short to be real
        '{"summary": "O diploma cria um apoio à renda para famílias elegíveis."}',  # no headline
        f'{{{headline.replace("renda", "renda" * 40)}, "summary": "Um resumo suficientemente'
        ' longo."}',  # a paragraph masquerading as a headline
    ]
    for payload in cases:
        with pytest.raises(SummaryError):
            summarize_act(FakeProvider(payload), RequestBudget(10), "t", "s", "x")


def test_group_acts_parses_valid_grouping() -> None:
    from src.pipeline.group_related import group_acts

    payload = '{"groups": [{"label": "Igualdade no trabalho", "member_ids": [1, 3]}]}'
    acts = [("Resolução n.º 190/2026", "h1"), ("Portaria n.º 296/2026", "h2"),
            ("Resolução n.º 191/2026", "h3")]  # fmt: skip
    groups = group_acts(FakeProvider(payload), RequestBudget(10), acts)
    assert len(groups) == 1
    assert groups[0].member_ids == [1, 3]


def test_group_acts_rejects_broken_groupings() -> None:
    from src.pipeline.group_related import GroupingError, group_acts

    acts = [("t1", "h1"), ("t2", "h2")]
    cases = [
        '{"groups": [{"label": "xxx", "member_ids": [1]}]}',  # a group of one is not a group
        '{"groups": [{"label": "xxx", "member_ids": [1, 5]}]}',  # unknown act id
        '{"groups": [{"label": "xxx", "member_ids": [1, 2]},'
        ' {"label": "yyy", "member_ids": [2, 1]}]}',  # an act cannot be in two groups
        "not json at all",
    ]
    for payload in cases:
        with pytest.raises(GroupingError):
            group_acts(FakeProvider(payload), RequestBudget(10), acts)


def test_act_rank_orders_law_before_recommendation_before_retification() -> None:
    from src.pipeline.show_digest import act_rank

    ordered = [
        "Decreto-Lei n.º 97/2026",
        "Portaria n.º 296/2026/1",
        "Resolução do Conselho de Ministros n.º 1/2026",
        "Resolução da Assembleia da República n.º 190/2026",
        "Declaração de Retificação n.º 26/2026/1",
    ]
    ranks = [act_rank(t) for t in ordered]
    assert ranks == sorted(ranks)
    assert act_rank("Coisa Nova n.º 1/2026") < act_rank("Declaração de Retificação n.º 2/2026")


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


def test_gemini_retries_429_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    from src.pipeline import providers as prov

    sleeps: list[float] = []
    monkeypatch.setattr(prov.time, "sleep", lambda s: sleeps.append(s))
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:  # two 429s, then success
            return httpx.Response(429)
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": GOOD}]}}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = prov.GeminiProvider("key", client=client)
    assert provider.complete_json("p", {}) == GOOD
    assert calls["n"] == 3
    assert sleeps == [15.0, 30.0]  # exponential backoff between attempts
