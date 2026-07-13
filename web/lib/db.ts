// Read-only data access for the site. The Vercel env carries the web_ro role's URL —
// the site cannot write, by database grant, not by discipline.
import { neon } from "@neondatabase/serverless";

const sql = neon(process.env.DATABASE_URL!);

export const THEME_ORDER = ["habitacao", "saude", "economia", "outros"] as const;
export const THEME_LABEL: Record<string, string> = {
  habitacao: "Habitação",
  saude: "Saúde",
  economia: "Economia",
  outros: "Outros",
};

const PROMPT_VERSION = "v1";

export interface DigestEntry {
  act_title: string;
  themes: string[];
  headline: string | null; // null on pre-v1 rows only; display falls back to act_title
  summary_plain: string;
  pdf_url: string;
  flagged: boolean;
}

// Normative weight of an act, from its official designation: acts that change the law
// outrank recommendations, which outrank typo corrections. Mirrors act_rank in
// src/pipeline/show_digest.py — keep the two in sync.
const ACT_RANK: [string, number][] = [
  ["lei orgânica", 0],
  ["lei ", 0],
  ["decreto-lei", 0],
  ["decreto legislativo regional", 0],
  ["decreto do presidente", 1],
  ["decreto regulamentar", 1],
  ["portaria", 1],
  ["resolução do conselho de ministros", 2],
  ["acórdão", 2],
  ["resolução", 3],
  ["declaração de retificação", 5],
];

export function actRank(actTitle: string): number {
  const title = actTitle.toLowerCase();
  for (const [prefix, rank] of ACT_RANK) if (title.startsWith(prefix)) return rank;
  return 4;
}

// Official-gazette shorthand for the act type — the compact list's typographic stamp.
// Unlike a theme photo, this mark is informative: it says what the act IS.
const ACT_MONOGRAM: [string, string][] = [
  ["lei orgânica", "LO"],
  ["lei ", "LEI"],
  ["decreto-lei", "DL"],
  ["decreto legislativo regional", "DLR"],
  ["decreto do presidente", "DPR"],
  ["decreto regulamentar", "DR"],
  ["portaria", "PORT"],
  ["resolução do conselho de ministros", "RCM"],
  ["resolução da assembleia da república", "RAR"],
  ["resolução da assembleia legislativa", "RAL"],
  ["acórdão", "AC"],
  ["declaração de retificação", "RET"],
];

export function actMonogram(actTitle: string): string {
  const title = actTitle.toLowerCase();
  for (const [prefix, monogram] of ACT_MONOGRAM) if (title.startsWith(prefix)) return monogram;
  return "§";
}

export interface StoryGroup {
  label: string;
  pdf_urls: string[];
}

export interface ArchiveDay {
  pub_date: string;
  n: number;
}

export interface PipelineRun {
  id: number;
  queued: number;
  analysed: number;
  flagged: number;
  failed: number;
  deferred: number;
  citation_ok: number;
  citation_total: number;
  model_name: string;
  created_at: string;
}

export async function latestDigestDate(): Promise<string | null> {
  const rows = (await sql`
    select max(g.pub_date)::text as d
    from raw.gazette_item g
    join digest.act_analysis a on a.pdf_url = g.pdf_url
    where a.prompt_version = ${PROMPT_VERSION}
  `) as { d: string | null }[];
  return rows[0]?.d ?? null;
}

export async function digestFor(date: string): Promise<DigestEntry[]> {
  const rows = (await sql`
    select g.act_title,
           a.themes,
           a.headline,
           a.summary_plain,
           g.pdf_url,
           cardinality(a.ungrounded_numbers) > 0 as flagged
    from raw.gazette_item g
    join digest.act_analysis a on a.pdf_url = g.pdf_url
    where g.pub_date = ${date} and a.prompt_version = ${PROMPT_VERSION}
  `) as DigestEntry[];
  const order = (e: DigestEntry) => THEME_ORDER.indexOf(e.themes[0] as never);
  return rows.sort(
    (x, y) =>
      order(x) - order(y) ||
      actRank(x.act_title) - actRank(y.act_title) ||
      x.act_title.localeCompare(y.act_title)
  );
}

export async function previousDigestDate(before: string): Promise<string | null> {
  const rows = (await sql`
    select max(g.pub_date)::text as d
    from raw.gazette_item g
    join digest.act_analysis a on a.pdf_url = g.pdf_url
    where a.prompt_version = ${PROMPT_VERSION} and g.pub_date < ${before}
  `) as { d: string | null }[];
  return rows[0]?.d ?? null;
}

export async function nextDigestDate(after: string): Promise<string | null> {
  const rows = (await sql`
    select min(g.pub_date)::text as d
    from raw.gazette_item g
    join digest.act_analysis a on a.pdf_url = g.pdf_url
    where a.prompt_version = ${PROMPT_VERSION} and g.pub_date > ${after}
  `) as { d: string | null }[];
  return rows[0]?.d ?? null;
}

export interface ThemeEntry extends DigestEntry {
  pub_date: string;
}

export async function themeEntries(theme: string): Promise<ThemeEntry[]> {
  const rows = (await sql`
    select g.act_title,
           a.themes,
           a.headline,
           a.summary_plain,
           g.pdf_url,
           cardinality(a.ungrounded_numbers) > 0 as flagged,
           g.pub_date::text as pub_date
    from raw.gazette_item g
    join digest.act_analysis a on a.pdf_url = g.pdf_url
    where a.prompt_version = ${PROMPT_VERSION} and ${theme} = any(a.themes)
    order by g.pub_date desc, g.act_title
  `) as ThemeEntry[];
  return rows;
}

export async function dayGrouping(date: string): Promise<StoryGroup[]> {
  // Latest grouping version for the day; no row (or an empty list) renders ungrouped.
  const rows = (await sql`
    select groups
    from digest.day_grouping
    where pub_date = ${date} and prompt_version = ${PROMPT_VERSION}
    order by id desc
    limit 1
  `) as { groups: StoryGroup[] }[];
  return rows[0]?.groups ?? [];
}

export async function archiveDays(): Promise<ArchiveDay[]> {
  return (await sql`
    select g.pub_date::text as pub_date, count(*)::int as n
    from raw.gazette_item g
    join digest.act_analysis a on a.pdf_url = g.pdf_url
    where a.prompt_version = ${PROMPT_VERSION}
    group by g.pub_date
    order by g.pub_date desc
  `) as ArchiveDay[];
}

export async function pipelineRuns(limit = 30): Promise<PipelineRun[]> {
  return (await sql`
    select id, queued, analysed, flagged, failed, deferred,
           citation_ok, citation_total, model_name, created_at::text as created_at
    from evals.pipeline_run
    order by id desc
    limit ${limit}
  `) as PipelineRun[];
}
