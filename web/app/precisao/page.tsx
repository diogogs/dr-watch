import { pipelineRuns } from "@/lib/db";

export const revalidate = 3600;

export default async function Precisao() {
  const runs = await pipelineRuns();
  const analysed = runs.reduce((s, r) => s + r.analysed, 0);
  const flagged = runs.reduce((s, r) => s + r.flagged, 0);
  const citOk = runs.reduce((s, r) => s + r.citation_ok, 0);
  const citTotal = runs.reduce((s, r) => s + r.citation_total, 0);
  const pct = (a: number, b: number) => (b === 0 ? "—" : `${Math.round((100 * a) / b)}%`);

  return (
    <div className="narrow">
      <h1>Quão fiável é isto?</h1>
      <p className="subtitle">
        Cada execução do sistema mede a sua própria qualidade e o resultado é publicado aqui,
        sem exceções. Nenhum destes números é editado à mão.
      </p>

      <div className="stats">
        <div>
          <strong>{analysed}</strong>
          <span>diplomas analisados</span>
        </div>
        <div>
          <strong>{pct(analysed - flagged, analysed)}</strong>
          <span>resumos com todos os números verificados na fonte</span>
        </div>
        <div>
          <strong>{pct(citOk, citTotal)}</strong>
          <span>citações oficiais que resolvem</span>
        </div>
      </div>

      <h2 className="theme-header">Como se mede</h2>
      <p style={{ color: "var(--ink-secondary)", margin: "0.6rem 0 1.4rem" }}>
        Todos os números de cada resumo têm de existir no documento oficial (verificação
        determinística — resumos que falham são assinalados, não escondidos). Todas as ligações
        aos PDFs oficiais são testadas em cada execução. A exatidão da classificação temática
        será medida contra um conjunto de teste etiquetado à mão, em preparação.
      </p>

      <h2 className="theme-header">Execuções recentes</h2>
      <table>
        <thead>
          <tr>
            <th>Quando (UTC)</th>
            <th>Em fila</th>
            <th>Analisados</th>
            <th>Assinalados</th>
            <th>Falhas</th>
            <th>Citações</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.id}>
              <td>{r.created_at.slice(0, 16)}</td>
              <td>{r.queued}</td>
              <td>{r.analysed}</td>
              <td>{r.flagged}</td>
              <td>{r.failed}</td>
              <td>
                {r.citation_ok}/{r.citation_total}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
