import { DigestEntry, StoryGroup, THEME_LABEL, THEME_ORDER, actRank } from "@/lib/db";
import { THEME_IMAGES } from "@/lib/images";
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

// Deterministic image assignment: walk the day's image-bearing cards in display order,
// cycling through each theme's curated pool so same-theme cards differ within the day.
function imagePicker() {
  const counters = new Map<string, number>();
  return (theme: string): string | null => {
    const pool = THEME_IMAGES[theme];
    if (!pool || pool.length === 0) return null;
    const i = counters.get(theme) ?? 0;
    counters.set(theme, i + 1);
    return pool[i % pool.length].src;
  };
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
  // Observador-style asymmetric front: hero (image) → mid column with one pictured
  // secondary + a compact thumbnail list (the tail) → right column, text only.
  const [hero, secondary, ...tail] = stories;
  const nRight = Math.min(4, Math.ceil(tail.length / 2));
  const right = tail.slice(0, nRight);
  const compact = tail.slice(nRight);
  const pick = imagePicker();
  const heroImg = hero ? pick(hero.lead.themes[0]) : null;
  const secondaryImg = secondary ? pick(secondary.lead.themes[0]) : null;
  const compactImgs = compact.map((s) => pick(s.lead.themes[0]));

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

      <div className="front">
        <div className="col-left">
          {hero && (
            <article className="story hero">
              {heroImg && <Thumb src={heroImg} />}
              <Kicker e={hero.lead} />
              <h2>{hero.lead.headline ?? hero.lead.act_title}</h2>
              <p>{hero.lead.summary_plain}</p>
              <Flag e={hero.lead} />
              <Official e={hero.lead} />
              <Related story={hero} />
            </article>
          )}
        </div>

        <div className="col-mid">
          {secondary && (
            <article className="story secondary">
              {secondaryImg && <Thumb src={secondaryImg} />}
              <Kicker e={secondary.lead} />
              <h3>{secondary.lead.headline ?? secondary.lead.act_title}</h3>
              <p className="clamp">{secondary.lead.summary_plain}</p>
              <Flag e={secondary.lead} />
              <Official e={secondary.lead} />
              <Related story={secondary} />
            </article>
          )}
          {compact.length > 0 && (
            <div className="compact-list">
              {compact.map((s, i) => (
                <article className="compact-item" key={s.lead.pdf_url}>
                  {compactImgs[i] && <Thumb src={compactImgs[i]} small />}
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

        <div className="col-right">
          {right.map((s) => (
            <article className="story text-story" key={s.lead.pdf_url}>
              <Kicker e={s.lead} />
              <h3>{s.lead.headline ?? s.lead.act_title}</h3>
              <p>{s.lead.summary_plain}</p>
              <Flag e={s.lead} />
              <Official e={s.lead} />
              <Related story={s} />
            </article>
          ))}
        </div>
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

function Thumb({ src, small = false }: { src: string; small?: boolean }) {
  return (
    <div className={small ? "thumb thumb-sm" : "thumb"}>
      {/* decorative, theme-level illustration — not a photo of the act's subject */}
      <img src={src} alt="" loading={small ? "lazy" : "eager"} />
    </div>
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
