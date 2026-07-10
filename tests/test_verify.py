"""Number-grounding checks — the deterministic guardrail before publication."""

from __future__ import annotations

from src.pipeline.verify import ungrounded_numbers


def test_grounded_summary_passes() -> None:
    source = "Portaria n.º 294/2026. Fixa a taxa em 23 % a partir de 1 de setembro de 2026."
    summary = "A taxa passa a ser de 23% em setembro de 2026."
    assert ungrounded_numbers(summary, source) == []


def test_invented_amount_is_flagged() -> None:
    source = "O apoio é atribuído aos agregados elegíveis nos termos do artigo 4.º."
    summary = "O apoio é de 350 euros por agregado."
    assert ungrounded_numbers(summary, source) == ["350"]


def test_decimal_comma_and_dot_are_equivalent() -> None:
    source = "A percentagem é fixada em 1,5 %."
    summary = "A percentagem fixada é 1.5%."
    assert ungrounded_numbers(summary, source) == []


def test_act_identity_numbers_are_grounded_via_title() -> None:
    source = "Decreto-Lei n.º 136/2026\nAltera o regime em vigor."
    summary = "O Decreto-Lei n.º 136/2026 altera o regime."
    assert ungrounded_numbers(summary, source) == []
