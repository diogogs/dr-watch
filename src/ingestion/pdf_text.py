"""Download DR act PDFs and extract normalised text for the LLM pipeline.

INCM PDFs carry embedded text (verified on real files, 2026-07-10 — no OCR needed), but the
raw extraction has two artefacts worth cleaning before any prompt sees it: a repeated page
header (page number, date, issue number, series — one line each) and hyphenated line breaks
("Regula -\\nmento"). The output is whitespace-normalised into a single string, which also
makes the future citation-validity check (excerpt matching) straightforward.
"""

from __future__ import annotations

import io
import re

import httpx
from pypdf import PdfReader

# Page-header lines, one pattern per line as extracted by pypdf. Unambiguous in body text.
_HEADER_LINE_RES = (
    re.compile(r"^\d+/\d+$"),  # "1/3" — page x of y
    re.compile(r"^\d{2}-\d{2}-\d{4}$"),  # issue date
    re.compile(r"^N\.º \d+$"),  # issue number
    re.compile(r"^\d+\.ª série$"),  # series
)

# "Regula -\nmento" → "Regulamento": hyphen at line end followed by a lowercase continuation.
_HYPHEN_BREAK_RE = re.compile(r"(\w) ?-\s*\n\s*(?=[a-záàâãéêíóôõúç])")


class PdfTextError(Exception):
    """The PDF could not be read or yielded no text."""


def _strip_header_lines(page_text: str) -> str:
    lines = page_text.splitlines()
    kept = [ln for ln in lines if not any(rx.match(ln.strip()) for rx in _HEADER_LINE_RES)]
    return "\n".join(kept)


def _dehyphenate(text: str) -> str:
    return _HYPHEN_BREAK_RE.sub(r"\1", text)


def extract_act_text(pdf_bytes: bytes) -> str:
    """Text of an act PDF: headers stripped, hyphenation joined, whitespace normalised."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise PdfTextError(f"could not read PDF: {exc!r}") from exc

    joined = "\n".join(_strip_header_lines(p) for p in pages)
    text = " ".join(_dehyphenate(joined).split())
    if not text:
        raise PdfTextError("PDF yielded no extractable text")
    return text


def fetch_pdf(url: str, client: httpx.Client | None = None) -> bytes:
    """Download an act PDF from files.diariodarepublica.pt."""
    owns = client is None
    client = client or httpx.Client(timeout=60)
    try:
        response = client.get(url)
        response.raise_for_status()
        return response.content
    finally:
        if owns:
            client.close()
