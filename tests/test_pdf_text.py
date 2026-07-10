"""PDF text extraction tests against a real INCM PDF (Decreto-Lei n.º 136/2026, 3 pages)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ingestion.pdf_text import PdfTextError, _dehyphenate, _strip_header_lines, extract_act_text

FIXTURE = Path(__file__).parent / "fixtures" / "decreto-lei-136-2026.pdf"


def test_real_pdf_extracts_clean_text() -> None:
    text = extract_act_text(FIXTURE.read_bytes())
    assert "Decreto-Lei n.º 136/2026" in text
    assert "Fundo Europeu" in text
    # hyphenated line break in the source ("Regula -/mento") must come out joined
    assert "Regulamento (CEE)" in text
    # page-header artefacts must be gone; whitespace fully normalised
    assert "1/3" not in text
    assert "1.ª série" not in text
    assert "\n" not in text and "  " not in text


def test_dehyphenate_joins_breaks_but_keeps_real_hyphens() -> None:
    assert _dehyphenate("Regula -\nmento") == "Regulamento"
    assert _dehyphenate("regula-\nmento") == "regulamento"
    # a real compound followed by a line break is not a hyphenation artefact
    assert "Decreto-Lei" in _dehyphenate("o Decreto-Lei\nseguinte")


def test_strip_header_lines_only_touches_header_patterns() -> None:
    page = "2/3\n10-07-2026\nN.º 132\n1.ª série\nArtigo 1.º\nO presente decreto-lei..."
    assert _strip_header_lines(page) == "Artigo 1.º\nO presente decreto-lei..."


def test_garbage_bytes_raise() -> None:
    with pytest.raises(PdfTextError):
        extract_act_text(b"isto nao e um pdf")
