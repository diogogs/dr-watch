# ADR-002: Same-subject story grouping and a typographic front page (no stock photos)

**Date:** 2026-07-13 · **Status:** accepted

## Context

Same-day acts often arrive in packs — two AR resolutions on the same policy, an act and its
correction — and one card per act made one story read as several. Separately, the author
wanted the digest to feel like a news front page (hierarchy, scanability); news sites get
this from photo-led layouts, but the gazette has no images and the product's register is
sober rigour.

## Options

1. Merge related acts into one LLM-written combined summary.
2. Group at presentation level only: one "story card" per subject — lead act in full,
   related acts as compact sub-entries, every act keeping its own headline and citation.
3. No grouping; rely on adjacency in the list.

For visuals: (a) stock photos per theme, (b) AI-generated images, (c) typographic front
page with restrained per-theme color.

## Decision

**Option 2 + (c).** A new pipeline step (`group_related.py`) sends ONE extra request per
day listing the day's official titles + headlines; the model returns subject clusters
(groups of ≥2 only). A deterministic validator rejects unknown ids or an act in two groups;
a rejected or absent grouping renders ungrouped — grouping can never break a digest.
Groupings are APPEND-ONLY (`digest.day_grouping`, migration 0005): a day is re-grouped in a
new row when late acts land; the site reads the latest row per (day, prompt version).

Front page: the day's most consequential act (deterministic `actRank`) becomes the lead
story (large serif headline); the rest flow in a hairline grid with colored theme kickers
and a theme-count strip under the date. Photos were rejected: with no real imagery of the
events, theme stock photos repeat by day three and decorate without informing — the
credibility cost lands exactly on the product's core promise. Share links get a typographic
OG image (`next/og`) in the navy identity instead.

## Why

- Presentation-only grouping preserves the trust unit (one act → one citation → one
  grounded summary); merging summaries would create a cross-document hallucination surface
  the number-grounding check cannot see.
- +1 request/day is noise against the free tier; validation is free and deterministic.
- Newspaper hierarchy is achievable with typography alone — that is how front pages worked
  before photojournalism; it reads as authority, not absence.

## Consequences

- The site composes stories client-side of the query (`compose()` in `digest.tsx`): missing
  or stale group members degrade to single cards silently.
- Grouping quality is not yet measured; it joins the sampled-manual-judgement bucket. If it
  proves noisy, the conservative prompt ("when in doubt, do not group") tightens first.
- `/precisao` is unaffected: grouping writes no per-act analysis rows.
