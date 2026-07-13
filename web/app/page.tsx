import { dayGrouping, digestFor, latestDigestDate, previousDigestDate } from "@/lib/db";
import { Digest } from "./digest";

export const revalidate = 3600; // the gazette changes once a day; ISR keeps Neon asleep

export default async function Home() {
  const date = await latestDigestDate();
  if (!date) {
    return (
      <>
        <h1>Ainda sem edições analisadas</h1>
        <p className="subtitle">O primeiro digest aparece após a próxima publicação da Série I.</p>
      </>
    );
  }
  const [entries, groups, prevDate] = await Promise.all([
    digestFor(date),
    dayGrouping(date),
    previousDigestDate(date),
  ]);
  return (
    <Digest date={date} entries={entries} groups={groups} prevDate={prevDate} nextDate={null} />
  );
}
