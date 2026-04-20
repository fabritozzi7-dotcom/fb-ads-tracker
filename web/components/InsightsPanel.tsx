"use client";

import { useEffect, useState } from "react";

interface CompetitorInsight {
  tonos: Record<string, number>;
  topCtas: [string, number][];
  topKeywords: [string, number][];
  avgClaridad: number;
  avgUrgencia: number;
  count: number;
}

interface InsightsData {
  insights: Record<string, CompetitorInsight>;
  globalKeywords: [string, number][];
  totalAnalyzed: number;
}

const TONO_COLORS: Record<string, string> = {
  emocional: "bg-pink-500",
  racional: "bg-sky-500",
  urgente: "bg-red-500",
  aspiracional: "bg-amber-500",
  informativo: "bg-emerald-500",
};

const COMP_ACCENT: Record<string, string> = {
  "Universidad Blas Pascal": "text-blue-600 dark:text-blue-400",
  "Universidad Católica de Córdoba": "text-purple-600 dark:text-purple-400",
};

export default function InsightsPanel() {
  const [data, setData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/insights")
      .then((r) => r.json())
      .then((d) => setData(d))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-40 animate-pulse rounded-xl bg-zinc-200 dark:bg-zinc-800" />
        ))}
      </div>
    );
  }

  if (!data || data.totalAnalyzed === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-zinc-300 dark:border-zinc-700">
        <p className="text-zinc-500 dark:text-zinc-400">
          No hay analisis de IA disponibles. Ejecuta el analyzer primero.
        </p>
      </div>
    );
  }

  const competitors = Object.entries(data.insights);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
          Insights IA
        </h2>
        <span className="text-xs text-zinc-500 dark:text-zinc-400">
          {data.totalAnalyzed} anuncios analizados
        </span>
      </div>

      {/* Competitor comparison grid */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {competitors.map(([comp, insight]) => (
          <div
            key={comp}
            className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <h3 className={`mb-3 text-sm font-bold ${COMP_ACCENT[comp] || "text-zinc-900 dark:text-zinc-100"}`}>
              {comp}
              <span className="ml-2 text-xs font-normal text-zinc-400">
                ({insight.count} anuncios)
              </span>
            </h3>

            {/* Tonos distribution */}
            <div className="mb-4">
              <p className="mb-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                Distribucion de tonos
              </p>
              <div className="flex h-3 overflow-hidden rounded-full">
                {Object.entries(insight.tonos)
                  .sort((a, b) => b[1] - a[1])
                  .map(([tono, count]) => {
                    const pct = (count / insight.count) * 100;
                    return (
                      <div
                        key={tono}
                        className={`${TONO_COLORS[tono] || "bg-zinc-400"}`}
                        style={{ width: `${pct}%` }}
                        title={`${tono}: ${count} (${pct.toFixed(0)}%)`}
                      />
                    );
                  })}
              </div>
              <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5">
                {Object.entries(insight.tonos)
                  .sort((a, b) => b[1] - a[1])
                  .map(([tono, count]) => (
                    <span key={tono} className="flex items-center gap-1 text-[10px] text-zinc-500 dark:text-zinc-400">
                      <span className={`inline-block h-2 w-2 rounded-full ${TONO_COLORS[tono] || "bg-zinc-400"}`} />
                      {tono} ({count})
                    </span>
                  ))}
              </div>
            </div>

            {/* Avg scores */}
            <div className="mb-4 grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-zinc-50 p-2.5 dark:bg-zinc-800">
                <p className="text-[10px] uppercase tracking-wider text-zinc-500">Claridad</p>
                <p className="text-xl font-bold text-zinc-900 dark:text-zinc-100">{insight.avgClaridad}</p>
                <div className="mt-1 h-1 rounded-full bg-zinc-200 dark:bg-zinc-700">
                  <div
                    className="h-1 rounded-full bg-violet-500"
                    style={{ width: `${insight.avgClaridad * 10}%` }}
                  />
                </div>
              </div>
              <div className="rounded-lg bg-zinc-50 p-2.5 dark:bg-zinc-800">
                <p className="text-[10px] uppercase tracking-wider text-zinc-500">Urgencia</p>
                <p className="text-xl font-bold text-zinc-900 dark:text-zinc-100">{insight.avgUrgencia}</p>
                <div className="mt-1 h-1 rounded-full bg-zinc-200 dark:bg-zinc-700">
                  <div
                    className="h-1 rounded-full bg-orange-500"
                    style={{ width: `${insight.avgUrgencia * 10}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Top CTAs */}
            <div className="mb-3">
              <p className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                CTAs mas usados
              </p>
              <div className="space-y-0.5">
                {insight.topCtas.slice(0, 3).map(([cta, count]) => (
                  <div key={cta} className="flex items-center justify-between">
                    <span className="truncate text-xs text-zinc-700 dark:text-zinc-300">
                      &ldquo;{cta}&rdquo;
                    </span>
                    <span className="ml-2 text-[10px] text-zinc-400">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Top keywords */}
            <div>
              <p className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                Palabras clave
              </p>
              <div className="flex flex-wrap gap-1">
                {insight.topKeywords.slice(0, 10).map(([kw, count]) => (
                  <span
                    key={kw}
                    className="rounded-md bg-zinc-200 px-1.5 py-0.5 text-[10px] text-zinc-700 dark:bg-zinc-700 dark:text-zinc-300"
                  >
                    {kw} ({count})
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Global keyword cloud */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <h3 className="mb-3 text-sm font-bold text-zinc-900 dark:text-zinc-100">
          Palabras clave globales
        </h3>
        <div className="flex flex-wrap gap-2">
          {data.globalKeywords.map(([kw, count], i) => {
            const size = i < 3 ? "text-base" : i < 8 ? "text-sm" : "text-xs";
            const weight = i < 5 ? "font-bold" : "font-medium";
            return (
              <span
                key={kw}
                className={`rounded-lg bg-violet-100 px-2.5 py-1 text-violet-800 dark:bg-violet-900 dark:text-violet-300 ${size} ${weight}`}
              >
                {kw}
                <span className="ml-1 opacity-60">({count})</span>
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}
