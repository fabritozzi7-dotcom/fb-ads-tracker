"use client";

import { useCallback, useState } from "react";

interface FilterBarProps {
  competidores: string[];
  onFilterChange: (filters: {
    competidor: string;
    estado: string;
    busqueda: string;
  }) => void;
}

export default function FilterBar({
  competidores,
  onFilterChange,
}: FilterBarProps) {
  const [competidor, setCompetidor] = useState("todos");
  const [estado, setEstado] = useState("todos");
  const [busqueda, setBusqueda] = useState("");

  const emit = useCallback(
    (patch: { competidor?: string; estado?: string; busqueda?: string }) => {
      const next = {
        competidor: patch.competidor ?? competidor,
        estado: patch.estado ?? estado,
        busqueda: patch.busqueda ?? busqueda,
      };
      onFilterChange(next);
    },
    [competidor, estado, busqueda, onFilterChange]
  );

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      {/* Competidor */}
      <select
        value={competidor}
        onChange={(e) => {
          setCompetidor(e.target.value);
          emit({ competidor: e.target.value });
        }}
        className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
      >
        <option value="todos">Todos los competidores</option>
        {competidores.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>

      {/* Estado */}
      <select
        value={estado}
        onChange={(e) => {
          setEstado(e.target.value);
          emit({ estado: e.target.value });
        }}
        className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
      >
        <option value="todos">Todos los estados</option>
        <option value="activo">Activos</option>
        <option value="inactivo">Inactivos</option>
      </select>

      {/* Busqueda */}
      <div className="relative flex-1">
        <input
          type="text"
          placeholder="Buscar en texto del anuncio..."
          value={busqueda}
          onChange={(e) => {
            setBusqueda(e.target.value);
            emit({ busqueda: e.target.value });
          }}
          className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 pl-9 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
        />
        <svg
          className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>
    </div>
  );
}
