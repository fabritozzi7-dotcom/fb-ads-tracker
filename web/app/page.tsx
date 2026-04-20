"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Ad } from "@/lib/supabase";
import AdCard from "@/components/AdCard";
import FilterBar from "@/components/FilterBar";
import StatsBar from "@/components/StatsBar";
import InsightsPanel from "@/components/InsightsPanel";

const COMPETIDORES = [
  "Universidad Blas Pascal",
  "Universidad Católica de Córdoba",
];

interface AdsResponse {
  ads: Ad[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

type Tab = "anuncios" | "insights";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>("anuncios");
  const [ads, setAds] = useState<Ad[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({
    total: 0,
    activos: 0,
    porCompetidor: {} as Record<string, number>,
  });

  const filtersRef = useRef({
    competidor: "todos",
    estado: "todos",
    busqueda: "",
  });
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const fetchAds = useCallback(async (pageNum: number) => {
    setLoading(true);
    const f = filtersRef.current;
    const params = new URLSearchParams({
      page: String(pageNum),
      ...(f.competidor !== "todos" && { competidor: f.competidor }),
      ...(f.estado !== "todos" && { estado: f.estado }),
      ...(f.busqueda && { busqueda: f.busqueda }),
    });

    try {
      setError(null);
      const res = await fetch(`/api/ads?${params}`);
      const data = await res.json();
      if (!res.ok) {
        setError(`Error ${res.status}: ${data.error || "Unknown error"}${data.code ? ` (${data.code})` : ""}`);
        setAds([]);
        setTotal(0);
        return;
      }
      setAds(data.ads || []);
      setTotal(data.total || 0);
      setTotalPages(data.totalPages || 1);
      setPage(data.page);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(`Error de conexión: ${message}`);
      console.error("Error fetching ads:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await fetch("/api/ads?page=1");
        const data: AdsResponse = await res.json();
        const totalCount = data.total || 0;

        const resActive = await fetch("/api/ads?page=1&estado=activo");
        const dataActive: AdsResponse = await resActive.json();
        const activoCount = dataActive.total || 0;

        const porComp: Record<string, number> = {};
        for (const c of COMPETIDORES) {
          const r = await fetch(
            `/api/ads?page=1&competidor=${encodeURIComponent(c)}`
          );
          const d: AdsResponse = await r.json();
          porComp[c] = d.total || 0;
        }

        setStats({
          total: totalCount,
          activos: activoCount,
          porCompetidor: porComp,
        });
      } catch (err) {
        console.error("Error fetching stats:", err);
      }
    }
    fetchStats();
  }, []);

  useEffect(() => {
    fetchAds(1);
  }, [fetchAds]);

  const handleFilterChange = useCallback(
    (filters: { competidor: string; estado: string; busqueda: string }) => {
      filtersRef.current = filters;
      clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        fetchAds(1);
      }, 300);
    },
    [fetchAds]
  );

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      {/* Stats */}
      <div className="mb-6">
        <StatsBar
          total={stats.total}
          activos={stats.activos}
          porCompetidor={stats.porCompetidor}
        />
      </div>

      {/* Tabs */}
      <div className="mb-6 flex gap-1 rounded-lg bg-zinc-100 p-1 dark:bg-zinc-800">
        <button
          onClick={() => setActiveTab("anuncios")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "anuncios"
              ? "bg-white text-zinc-900 shadow-sm dark:bg-zinc-700 dark:text-zinc-100"
              : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
          }`}
        >
          Anuncios
        </button>
        <button
          onClick={() => setActiveTab("insights")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "insights"
              ? "bg-white text-zinc-900 shadow-sm dark:bg-zinc-700 dark:text-zinc-100"
              : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
          }`}
        >
          Insights IA
        </button>
      </div>

      {activeTab === "insights" ? (
        <InsightsPanel />
      ) : (
        <>
          {/* Filters */}
          <div className="mb-6">
            <FilterBar
              competidores={COMPETIDORES}
              onFilterChange={handleFilterChange}
            />
          </div>

          {/* Error banner */}
          {error && (
            <div className="mb-4 rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
              <p className="font-medium">Error al cargar anuncios</p>
              <p className="mt-1 font-mono text-xs">{error}</p>
            </div>
          )}

          {/* Results count */}
          <div className="mb-4 flex items-center justify-between">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              {loading ? "Cargando..." : `${total} anuncios encontrados`}
            </p>
            {totalPages > 1 && (
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Pagina {page} de {totalPages}
              </p>
            )}
          </div>

          {/* Grid */}
          {loading ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-80 animate-pulse rounded-xl bg-zinc-200 dark:bg-zinc-800"
                />
              ))}
            </div>
          ) : ads.length === 0 ? (
            <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-zinc-300 dark:border-zinc-700">
              <p className="text-zinc-500 dark:text-zinc-400">
                No se encontraron anuncios con esos filtros.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {ads.map((ad) => (
                <AdCard key={ad.id} ad={ad} />
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-2">
              <button
                onClick={() => fetchAds(page - 1)}
                disabled={page <= 1}
                className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium transition-colors hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-40 dark:border-zinc-700 dark:hover:bg-zinc-800"
              >
                Anterior
              </button>
              {Array.from({ length: Math.min(totalPages, 7) }).map((_, i) => {
                let pageNum: number;
                if (totalPages <= 7) {
                  pageNum = i + 1;
                } else if (page <= 4) {
                  pageNum = i + 1;
                } else if (page >= totalPages - 3) {
                  pageNum = totalPages - 6 + i;
                } else {
                  pageNum = page - 3 + i;
                }
                return (
                  <button
                    key={pageNum}
                    onClick={() => fetchAds(pageNum)}
                    className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      pageNum === page
                        ? "bg-violet-600 text-white"
                        : "border border-zinc-300 hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <button
                onClick={() => fetchAds(page + 1)}
                disabled={page >= totalPages}
                className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium transition-colors hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-40 dark:border-zinc-700 dark:hover:bg-zinc-800"
              >
                Siguiente
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
