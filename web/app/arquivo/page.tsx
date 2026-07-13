import { archiveDays } from "@/lib/db";
import { formatDate } from "@/lib/format";

export const revalidate = 3600;

export default async function Arquivo() {
  const days = await archiveDays();
  return (
    <div className="narrow">
      <h1>Arquivo</h1>
      <p className="subtitle">
        Todas as edições analisadas desde o arranque. O arquivo cresce um dia de cada vez —
        não há retroativos.
      </p>
      <div className="day-list">
        {days.map((d) => (
          <a key={d.pub_date} href={`/d/${d.pub_date}`}>
            {formatDate(d.pub_date)}
            <span>
              {d.n} {d.n === 1 ? "diploma" : "diplomas"}
            </span>
          </a>
        ))}
      </div>
    </div>
  );
}
