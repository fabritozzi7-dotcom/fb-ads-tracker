"""
Sincroniza anuncios del Meta Ads Archive hacia Supabase (tabla anuncios_competencia).

Variables de entorno (.env):
  SUPABASE_URL
  SUPABASE_KEY
  FACEBOOK_ACCESS_TOKEN

Opcionales:
  SEARCH_PAGE_IDS=comma,separated,page,ids
  MARK_STALE_INACTIVE=true|false   (default: true)
  META_GRAPH_VERSION=v19.0
  META_MAX_RETRIES=5
  META_INITIAL_BACKOFF_SECONDS=2.0
"""

from __future__ import annotations

import sys

from app.sync_service import configure_logging, sync_competitor_ads


def main() -> int:
    configure_logging()
    try:
        summary = sync_competitor_ads()
    except Exception as exc:  # noqa: BLE001 — CLI: mostrar causa al usuario
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    errors = summary.get("chunk_errors", 0)
    print("-- Sincronizacion completada --")
    print(f"  Paginas procesadas   : {', '.join(summary['page_ids'])}")
    print(f"  Ads enviados (upsert): {summary['upserted']}")
    print(f"  Ads marcados inactivos: {summary['marked_inactive']}")
    print(f"  Errores de chunk     : {errors}")
    if errors:
        print("  WARN: Algunos chunks fallaron. Revisa los logs para mas detalle.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
