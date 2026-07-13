# ADR-004: Scarce imagery on a two-column front; act-type stamps for the tail

**Date:** 2026-07-13 · **Status:** accepted (amends ADR-003's layout and image rules)

## Context

The three-column front with an image on most cards failed in review: 9 of the 13 pool
photos were buildings, so images differentiated nothing — habitação facades, São Bento and
the Baixa all read as "institutional architecture in navy". "Outros", the most frequent
theme, is a catch-all that no photograph can honestly represent, and its repeated São Bento
thumbnails looked broken. The author asked for two columns, importance deciding which
stories get images and how much space, and a rethink of what an image is for.

## Decision

**Images become a scarcity signal; identity for the tail comes from typographic stamps.**

- Two columns: main (hero with large photo + up to three full secondaries) and a side list
  ("Mais nesta edição") for the tail — tiers assigned from the existing normative-weight
  order, which IS the importance heuristic.
- At most two photos per page: the hero always (unless its theme is unpicturable), the
  first secondary only when its theme differs from the hero's. "outros" has no pool at all.
- The pool keeps only themes with a distinct visual language: habitação = facades,
  saúde = corridor/stethoscope, economia = euros/containers. Monument/cityscape photos
  (Baixa aérea, Arco da Rua Augusta, São Bento, night hospital) were removed — they are
  what made everything look like "a building".
- Side-list anchor = a stamp: the act-type shorthand (DL, PORT, RCM, RAR, RET…) set in
  serif inside a theme-colored square. Unlike a theme photo, the stamp is informative —
  it says what the act IS (law vs recommendation vs correction), never repeats badly, and
  echoes official-gazette aesthetics.
- Image assignment is deterministic by day-of-month over the pool, so consecutive days
  vary without render-time randomness.

## Why

- A photo on every card taught readers that photos mean nothing here; two per page makes
  them signal "this is today's lead". Scarcity restores meaning.
- The stamp solves the differentiation problem photos could not: the useful distinction
  between acts is their normative nature, which is exactly what the monogram encodes.
- Everything stays presentation-level: removing images entirely, if it comes to that, is a
  manifest prune plus one conditional.

## Consequences

- `/creditos` shrinks to 7 photographs; unused files were deleted from the repo.
- A hero classified "outros" renders text-only — acceptable: the large serif headline
  carries it.
- `actMonogram` (TS) joins `actRank`/`act_rank` as display logic derived from the official
  designation; it lives only in the web layer.
