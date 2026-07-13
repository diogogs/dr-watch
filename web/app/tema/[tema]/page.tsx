import { notFound } from "next/navigation";
import { THEME_LABEL, THEME_ORDER, themeEntries } from "@/lib/db";
import { formatDate } from "@/lib/format";

export const revalidate = 3600;

export default async function Tema({ params }: { params: Promise<{ tema: string }> }) {
  const { tema } = await params;
  if (!THEME_ORDER.includes(tema as never)) notFound();
  const entries = await themeEntries(tema);

  const days = new Map<string, typeof entries>();
  for (const e of entries) {
    const list = days.get(e.pub_date) ?? [];
    list.push(e);
    days.set(e.pub_date, list);
  }

  return (
    <div className="narrow">
      <h1>{THEME_LABEL[tema]}</h1>
      <p className="subtitle">
        Todos os diplomas classificados neste tema, do mais recente para o mais antigo.
      </p>
      {entries.length === 0 && <p>Ainda não há diplomas neste tema.</p>}
      {[...days.entries()].map(([day, list]) => (
        <section key={day}>
          <h2 className="theme-header">
            <a href={`/d/${day}`}>{formatDate(day)}</a>
          </h2>
          {list.map((e) => (
            <article className="story text-story" key={e.pdf_url}>
              <div className="kicker">
                <span className="kicker-act">{e.act_title}</span>
              </div>
              <h3>{e.headline ?? e.act_title}</h3>
              <p>{e.summary_plain}</p>
              <div className="official">
                <a href={e.pdf_url}>Documento oficial (PDF)</a>
              </div>
            </article>
          ))}
        </section>
      ))}
    </div>
  );
}
