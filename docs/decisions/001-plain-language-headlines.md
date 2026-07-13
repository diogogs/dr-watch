# ADR-001: Plain-language headlines (prompt v1), official designation demoted to metadata

**Date:** 2026-07-13 · **Status:** accepted

## Context

The first live digests headlined each entry with the act's official designation
("Portaria n.º 295/2026/1", "Resolução da Assembleia da República n.º 190/2026"). For a lay
reader that string carries zero information — knowing what any entry is about required
reading its full summary, which defeats the product's promise ("em linguagem humana") and
its front-page use case: scan the day in seconds. The summaries compounded it by opening
with the same designation ("A Portaria n.º 295/2026/1, de 13 de julho, adapta…"), pushing
substance to mid-sentence.

## Options

1. Keep the official title as headline; rely on summaries.
2. LLM-generated plain-language headline per act, official designation as kicker metadata.
3. Deterministic headline (truncate the official RSS summary).

## Decision

**Option 2.** The summarize step returns `{headline, summary}` in the same single request
(no budget increase). Headline contract: ≤ ~90 chars, European Portuguese, sober, says what
changes for whom, never the official designation. Summary rule added: lead with substance,
don't restate the designation. The deterministic number-grounding check now runs over
headline + summary combined. New nullable `digest.act_analysis.headline` column
(migration 0004); `PROMPT_VERSION` bumped to `v1`, which re-analyses history into new rows —
v0 rows stay as published (insert-only, charter principle 5). The site pins v1 and orders
entries within a theme by deterministic normative weight of the designation (law → rules →
recommendations → retifications), so the most consequential acts lead.

Option 3 was rejected because the official summaries are themselves legalese continuation
phrases ("Procede à alteração do…"), not headlines.

## Why

- The headline is the product: a front page whose headlines need the body text to be
  understood is a failed front page.
- One request still returns both fields, so the free-tier budget and pacing are unchanged.
- Grounding covers the new surface: an invented number in a headline flags the entry exactly
  like one in a summary.
- This is a new output field with new display semantics, not tuning of the classification
  prompt against vibes — the golden-set-before-tuning rule (charter principle 2) still holds
  for classification, whose prompt is untouched.

## Consequences

- Historical days are re-analysed under v1 (a deliberate, visible re-issue; v0 rows remain
  queryable). `/precisao` run history shows the backfill run like any other.
- `act_rank` (Python) and `actRank` (TypeScript) encode the same designation→weight table
  and must be kept in sync.
- Headline quality joins faithfulness in the "sampled manual judgement" bucket until the
  golden set exists; citation validity and number grounding stay the automatic gates.
