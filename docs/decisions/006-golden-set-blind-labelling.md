# ADR-006: Golden set — blind labelling CLI, overwritable ground truth, gated publication

**Date:** 2026-07-13 · **Status:** accepted

## Context

Charter principle 2: the golden set exists before any prompt is tuned, and /precisao
publicly promises "classification accuracy vs a hand-labelled set". The archive now grows
daily (~8–15 acts), so the author can start labelling toward the ~100-act target. The
design questions: what the labeller sees, how labels are stored, and when the public
number appears.

## Decision

- **Blind labelling.** The CLI (`uv run --env-file .env python -m src.evals.label`) shows
  the official title, the official RSS summary, the PDF link and (on request) a text
  excerpt — NEVER the model's classification. A golden set that has seen the model's
  answers inherits its mistakes and turns the accuracy metric into a circle.
- **Ordered multi-label input.** Letters map to themes, first = primary ("he" = habitação
  primary + economia). Mirrors the model's output contract (ordered theme list).
- **`evals.golden_label` is overwritable** (upsert by pdf_url, migration 0006) — unlike
  published outputs, ground truth is eval *input*; a mislabel is corrected, not versioned.
  The insert-only rule (charter principle 5) is about what readers saw, which this is not.
- **Gated publication.** /precisao shows the primary-theme accuracy only from 10 labels;
  below that it shows progress ("n/100 etiquetados"). A percentage over n<10 is noise
  wearing a number's clothes.
- Headline metric: primary-theme accuracy (model `themes[1]` == author `themes[1]`,
  joined at the current prompt version). Set-level agreement can join later.

## Consequences

- The labelling queue is derived (acts with text, no label), so sessions resume for free
  and each day's new acts simply appear at the end.
- Labels join acts, not prompt versions: when a prompt upgrade re-analyses history, the
  same labels grade the new version automatically — that is the point of a golden set.
- The `web_ro` role needs SELECT on new evals tables for the site to read the metric.
