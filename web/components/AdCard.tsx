"use client";

import { useState } from "react";
import type { Ad } from "@/lib/supabase";

const COMPETIDOR_COLORS: Record<string, string> = {
  "Universidad Blas Pascal":
    "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  "Universidad Católica de Córdoba":
    "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
};
const DEFAULT_COLOR =
  "bg-zinc-100 text-zinc-800 dark:bg-zinc-700 dark:text-zinc-300";

const TONO_COLORS: Record<string, string> = {
  emocional: "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-300",
  racional: "bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-300",
  urgente: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  aspiracional:
    "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
  informativo:
    "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300",
};

export default function AdCard({ ad }: { ad: Ad }) {
  const [expanded, setExpanded] = useState(false);
  const [showAi, setShowAi] = useState(false);

  const badgeColor = COMPETIDOR_COLORS[ad.competidor] || DEFAULT_COLOR;

  const text = ad.ad_text || "";
  const isLong = text.length > 180;
  const displayText = expanded || !isLong ? text : text.slice(0, 180) + "...";

  const ai = ad.ai_analysis;

  return (
    <div className="group flex flex-col overflow-hidden rounded-xl border border-zinc-200 bg-white transition-shadow hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900">
      {/* Image / Video thumbnail */}
      <div className="relative aspect-video w-full bg-zinc-100 dark:bg-zinc-800">
        {ad.image_url ? (
          <img
            src={ad.image_url}
            alt="Ad creative"
            className="h-full w-full object-cover"
          />
        ) : ad.video_url ? (
          <div className="flex h-full items-center justify-center">
            <svg
              className="h-12 w-12 text-zinc-400"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M8 5v14l11-7z" />
            </svg>
            <span className="ml-2 text-sm text-zinc-500">Video</span>
          </div>
        ) : (
          <div className="flex h-full items-center justify-center">
            <svg
              className="h-10 w-10 text-zinc-300 dark:text-zinc-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.41a2.25 2.25 0 013.182 0l2.909 2.91m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5z"
              />
            </svg>
          </div>
        )}

        {/* Active badge overlay */}
        <span
          className={`absolute right-2 top-2 rounded-full px-2 py-0.5 text-xs font-semibold ${
            ad.is_active
              ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
              : "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
          }`}
        >
          {ad.is_active ? "Activo" : "Inactivo"}
        </span>
      </div>

      {/* Content */}
      <div className="flex flex-1 flex-col p-4">
        {/* Competidor badge + date */}
        <div className="mb-2 flex items-center justify-between gap-2">
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${badgeColor}`}
          >
            {ad.competidor}
          </span>
          {ad.start_date && (
            <span className="text-xs text-zinc-500 dark:text-zinc-400">
              {new Date(ad.start_date + "T00:00:00").toLocaleDateString(
                "es-AR",
                {
                  day: "numeric",
                  month: "short",
                  year: "numeric",
                }
              )}
            </span>
          )}
        </div>

        {/* Page name */}
        {ad.page_name && (
          <p className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
            {ad.page_name}
          </p>
        )}

        {/* Ad text */}
        <div className="mb-3 flex-1">
          {displayText ? (
            <>
              <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
                {displayText}
              </p>
              {isLong && (
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="mt-1 text-xs font-medium text-violet-600 hover:text-violet-800 dark:text-violet-400"
                >
                  {expanded ? "Ver menos" : "Ver mas"}
                </button>
              )}
            </>
          ) : (
            <p className="text-sm italic text-zinc-400">Sin texto</p>
          )}
        </div>

        {/* AI Analysis expandible */}
        {ai && (
          <div className="mb-3">
            <button
              onClick={() => setShowAi(!showAi)}
              className="flex w-full items-center gap-1.5 rounded-lg bg-violet-50 px-3 py-1.5 text-xs font-medium text-violet-700 transition-colors hover:bg-violet-100 dark:bg-violet-950 dark:text-violet-300 dark:hover:bg-violet-900"
            >
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              {showAi ? "Ocultar analisis IA" : "Ver analisis IA"}
              <svg className={`ml-auto h-3 w-3 transition-transform ${showAi ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {showAi && (
              <div className="mt-2 space-y-2.5 rounded-lg border border-violet-100 bg-violet-50/50 p-3 dark:border-violet-900 dark:bg-violet-950/50">
                {/* Tono */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">Tono:</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${TONO_COLORS[ai.tono] || DEFAULT_COLOR}`}>
                    {ai.tono}
                  </span>
                </div>

                {/* CTA */}
                <div>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">CTA: </span>
                  <span className="text-xs font-medium text-zinc-800 dark:text-zinc-200">{ai.cta}</span>
                </div>

                {/* Publico objetivo */}
                <div>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">Publico: </span>
                  <span className="text-xs text-zinc-700 dark:text-zinc-300">{ai.publico_objetivo}</span>
                </div>

                {/* Propuesta de valor */}
                <div>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">Propuesta: </span>
                  <span className="text-xs text-zinc-700 dark:text-zinc-300">{ai.propuesta_valor}</span>
                </div>

                {/* Scores */}
                <div className="space-y-1.5">
                  <ScoreBar label="Claridad" score={ai.score_claridad} />
                  <ScoreBar label="Urgencia" score={ai.score_urgencia} />
                </div>

                {/* Keywords */}
                {ai.palabras_clave && ai.palabras_clave.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {ai.palabras_clave.map((kw) => (
                      <span
                        key={kw}
                        className="rounded-md bg-zinc-200 px-1.5 py-0.5 text-[10px] text-zinc-700 dark:bg-zinc-700 dark:text-zinc-300"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                )}

                {/* Resumen */}
                <p className="text-xs italic text-zinc-600 dark:text-zinc-400">
                  {ai.resumen}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-2">
          <a
            href={`https://www.facebook.com/ads/library/?id=${ad.ad_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 rounded-lg bg-violet-600 px-3 py-1.5 text-center text-xs font-medium text-white transition-colors hover:bg-violet-700"
          >
            Ver anuncio
          </a>
          {ad.landing_url && (
            <a
              href={ad.landing_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 rounded-lg border border-zinc-300 px-3 py-1.5 text-center text-xs font-medium text-zinc-700 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              Ver landing
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function ScoreBar({ label, score }: { label: string; score: number }) {
  const pct = Math.min(score, 10) * 10;
  const color =
    score >= 7
      ? "bg-green-500"
      : score >= 4
        ? "bg-amber-500"
        : "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <span className="w-14 text-xs text-zinc-500 dark:text-zinc-400">
        {label}
      </span>
      <div className="h-1.5 flex-1 rounded-full bg-zinc-200 dark:bg-zinc-700">
        <div
          className={`h-1.5 rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-5 text-right text-xs font-medium text-zinc-700 dark:text-zinc-300">
        {score}
      </span>
    </div>
  );
}
