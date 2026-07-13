import { notFound } from "next/navigation";
import { digestFor } from "@/lib/db";
import { Digest } from "../../digest";

export const revalidate = 3600;

export default async function Day({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params;
  // Shape AND calendar validity: "9999-99-99" matches the regex but is not a date, and
  // letting it through turns a bad URL into a Postgres cast error (500 instead of 404).
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || Number.isNaN(Date.parse(date))) notFound();
  const entries = await digestFor(date);
  if (entries.length === 0) notFound();
  return <Digest date={date} entries={entries} />;
}
