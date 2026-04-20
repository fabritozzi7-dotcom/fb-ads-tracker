"use client";

interface StatsBarProps {
  total: number;
  activos: number;
  porCompetidor: Record<string, number>;
}

export default function StatsBar({
  total,
  activos,
  porCompetidor,
}: StatsBarProps) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <StatCard label="Total anuncios" value={total} />
      <StatCard label="Activos" value={activos} accent />
      {Object.entries(porCompetidor).map(([nombre, count]) => (
        <StatCard key={nombre} label={nombre} value={count} />
      ))}
    </div>
  );
}

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent?: boolean;
}) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
        {label}
      </p>
      <p
        className={`mt-1 text-2xl font-bold ${
          accent
            ? "text-violet-600 dark:text-violet-400"
            : "text-zinc-900 dark:text-zinc-100"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
