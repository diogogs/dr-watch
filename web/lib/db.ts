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

const PROMPT_VERSION = "v0";

export interface DigestEntry {
  act_title: string;
  themes: string[];
  summary_plain: string;
  pdf_url: string;
  flagged: boolean;
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
           a.summary_plain,
           g.pdf_url,
           cardinality(a.ungrounded_numbers) > 0 as flagged
    from raw.gazette_item g
    join digest.act_analysis a on a.pdf_url = g.pdf_url
    where g.pub_date = ${date} and a.prompt_version = ${PROMPT_VERSION}
  `) as DigestEntry[];
  const order = (e: DigestEntry) => THEME_ORDER.indexOf(e.themes[0] as never);
  return rows.sort((x, y) => order(x) - order(y) || x.act_title.localeCompare(y.act_title));
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
