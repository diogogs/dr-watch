import { DigestEntry, StoryGroup, THEME_LABEL, THEME_ORDER, actMonogram, actRank } from "@/lib/db";
import { formatDate } from "@/lib/format";

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
  prevDate,
  nextDate,
}: {
  date: string;
  entries: DigestEntry[];
  groups: StoryGroup[];
  prevDate: string | null;
  nextDate: string | null;
}) {
  const stories = compose(entries, groups);
  // Two-column front, tiers by normative weight: hero + up to three full secondaries in
  // the main column; the tail as a compact, stamp-anchored list in the side column.
  const [hero, ...rest] = stories;
  const secondaries = rest.slice(0, 3);
  const side = rest.slice(3);

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
          <a key={t} href={`/tema/${t}`} className="strip-link">
            <i className={`dot t-${t}`} />
            {THEME_LABEL[t]} <strong>{n}</strong>
          </a>
        ))}
      </div>

      <div className={side.length > 0 ? "front" : "front front-single"}>
        <div className="col-main">
          {hero && (
            <article className="story hero">
              <Kicker e={hero.lead} />
              <h2>{hero.lead.headline ?? hero.lead.act_title}</h2>
              <p>{hero.lead.summary_plain}</p>
              <Flag e={hero.lead} />
              <Official e={hero.lead} />
              <Related story={hero} />
            </article>
          )}
          {secondaries.map((s) => (
            <article className="story secondary" key={s.lead.pdf_url}>
              <Kicker e={s.lead} />
              <h3>{s.lead.headline ?? s.lead.act_title}</h3>
              <p>{s.lead.summary_plain}</p>
              <Flag e={s.lead} />
              <Official e={s.lead} />
              <Related story={s} />
            </article>
          ))}
        </div>

        {side.length > 0 && (
          <div className="col-side">
            <div className="side-title">Mais nesta edição</div>
            {side.map((s) => (
              <article className="compact-item" key={s.lead.pdf_url}>
                <div className={`stamp t-${s.lead.themes[0]}`}>
                  {actMonogram(s.lead.act_title)}
                </div>
                <details>
                  <summary>
                    <Kicker e={s.lead} />
                    <span className="compact-headline">
                      {s.lead.headline ?? s.lead.act_title}
                    </span>
                  </summary>
                  <p>{s.lead.summary_plain}</p>
                  <Flag e={s.lead} />
                  <Official e={s.lead} />
                  <Related story={s} />
                </details>
              </article>
            ))}
          </div>
        )}
      </div>

      <div className="edition-nav">
        {prevDate ? (
          <a href={`/d/${prevDate}`}>← Edição anterior · {formatDate(prevDate)}</a>
        ) : (
          <span />
        )}
        <a href="/arquivo">Arquivo completo</a>
        {nextDate ? (
          <a href={`/d/${nextDate}`}>Edição seguinte · {formatDate(nextDate)} →</a>
        ) : (
          <span />
        )}
      </div>
    </>
  );
}

function Kicker({ e }: { e: DigestEntry }) {
  const theme = e.themes[0];
  return (
    <div className="kicker">
      <a className={`theme-tag t-${theme}`} href={`/tema/${theme}`}>
        {THEME_LABEL[theme]}
      </a>
      {e.headline && <span className="kicker-act"> · {e.act_title}</span>}
    </div>
  );
}

function Flag({ e }: { e: DigestEntry }) {
  if (!e.flagged) return null;
  return (
    <div className="flag">
      Números deste resumo não puderam ser verificados automaticamente — confirme no documento
      oficial.
    </div>
  );
}

function Official({ e }: { e: DigestEntry }) {
  return (
    <div className="official">
      <a href={e.pdf_url}>Documento oficial (PDF)</a>
    </div>
  );
}

function Related({ story }: { story: Story }) {
  if (story.related.length === 0) return null;
  return (
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
  );
}
