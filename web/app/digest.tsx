import { DigestEntry, THEME_LABEL, THEME_ORDER } from "@/lib/db";

export function Digest({ date, entries }: { date: string; entries: DigestEntry[] }) {
  return (
    <>
      <h1>Diário da República — Série I</h1>
      <p className="subtitle">
        {formatDate(date)} · {entries.length} {entries.length === 1 ? "diploma" : "diplomas"}
      </p>
      {THEME_ORDER.map((theme) => {
        const themed = entries.filter((e) => e.themes[0] === theme);
        if (themed.length === 0) return null;
        return (
          <section key={theme}>
            <div className="theme-header">{THEME_LABEL[theme]}</div>
            {themed.map((e) => (
              <article className="entry" key={e.pdf_url}>
                {e.headline && <div className="kicker">{e.act_title}</div>}
                <h3>{e.headline ?? e.act_title}</h3>
                <p>{e.summary_plain}</p>
                {e.flagged && (
                  <div className="flag">
                    Números deste resumo não puderam ser verificados automaticamente — confirme
                    no documento oficial.
                  </div>
                )}
                <div className="official">
                  <a href={e.pdf_url}>Documento oficial (PDF)</a>
                </div>
              </article>
            ))}
          </section>
        );
      })}
    </>
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
