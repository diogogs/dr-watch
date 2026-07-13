import { DigestEntry, StoryGroup, THEME_LABEL, THEME_ORDER, actRank } from "@/lib/db";

// A story is one subject: a lead act rendered in full plus related acts as sub-entries.
// Grouping is presentation-only — every act keeps its own headline and official citation.
interface Story {
  lead: DigestEntry;
  related: DigestEntry[];
}

const weight = (e: DigestEntry) =>
  actRank(e.act_title) * 100 + THEME_ORDER.indexOf(e.themes[0] as never);

const byWeight = (a: DigestEntry, b: DigestEntry) =>
  weight(a) - weight(b) || a.act_title.localeCompare(b.act_title);

function compose(entries: DigestEntry[], groups: StoryGroup[]): Story[] {
  const byUrl = new Map(entries.map((e) => [e.pdf_url, e]));
  const used = new Set<string>();
  const stories: Story[] = [];
  for (const g of groups) {
    const members = g.pdf_urls
      .map((u) => byUrl.get(u))
      .filter((e): e is DigestEntry => e !== undefined && !used.has(e.pdf_url));
    if (members.length < 2) continue; // degraded group — its members render as singles
    members.sort(byWeight);
    for (const m of members) used.add(m.pdf_url);
    stories.push({ lead: members[0], related: members.slice(1) });
  }
  for (const e of entries) if (!used.has(e.pdf_url)) stories.push({ lead: e, related: [] });
  return stories.sort((a, b) => byWeight(a.lead, b.lead));
}

export function Digest({
  date,
  entries,
  groups,
}: {
  date: string;
  entries: DigestEntry[];
  groups: StoryGroup[];
}) {
  const stories = compose(entries, groups);
  const [hero, ...rest] = stories;
  const counts = THEME_ORDER.map(
    (t) => [t, entries.filter((e) => e.themes[0] === t).length] as const
  ).filter(([, n]) => n > 0);

  return (
    <>
      <h1>Diário da República — Série I</h1>
      <p className="subtitle">
        {formatDate(date)} · {entries.length} {entries.length === 1 ? "diploma" : "diplomas"}
      </p>
      <div className="day-strip">
        {counts.map(([t, n]) => (
          <span key={t}>
            <i className={`dot t-${t}`} />
            {THEME_LABEL[t]} <strong>{n}</strong>
          </span>
        ))}
      </div>
      {hero && <StoryCard story={hero} hero />}
      <div className="story-grid">
        {rest.map((s) => (
          <StoryCard story={s} key={s.lead.pdf_url} />
        ))}
      </div>
    </>
  );
}

function StoryCard({ story, hero = false }: { story: Story; hero?: boolean }) {
  const e = story.lead;
  const theme = e.themes[0];
  const Headline: "h2" | "h3" = hero ? "h2" : "h3";
  return (
    <article className={hero ? "entry hero" : "entry"}>
      <div className="kicker">
        <span className={`theme-tag t-${theme}`}>{THEME_LABEL[theme]}</span>
        {e.headline && <span className="kicker-act"> · {e.act_title}</span>}
      </div>
      <Headline>{e.headline ?? e.act_title}</Headline>
      <p>{e.summary_plain}</p>
      {e.flagged && (
        <div className="flag">
          Números deste resumo não puderam ser verificados automaticamente — confirme no
          documento oficial.
        </div>
      )}
      <div className="official">
        <a href={e.pdf_url}>Documento oficial (PDF)</a>
      </div>
      {story.related.length > 0 && (
        <div className="related">
          <div className="related-title">No mesmo assunto</div>
          {story.related.map((r) => (
            <div className="related-item" key={r.pdf_url}>
              <a href={r.pdf_url}>{r.headline ?? r.act_title}</a>
              <span>
                {r.act_title} · PDF oficial
                {r.flagged && " · números por verificar"}
              </span>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

export function formatDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const months = [
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
  ];
  return `${d} de ${months[m - 1]} de ${y}`;
}
