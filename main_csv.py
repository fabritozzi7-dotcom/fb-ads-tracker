"""
Importa anuncios desde un archivo CSV/JSON local hacia Supabase.

Uso:
  python main_csv.py datos.csv
  python main_csv.py datos.json

El archivo debe contener datos de anuncios de la Meta Ad Library.
Ver app/csv_client.py para el formato esperado.
"""

from __future__ import annotations

import sys

from app.config import load_settings
from app.csv_client import CsvImportError, iter_ads_from_csv
from app.normalize import normalize_ad_row, utc_now_iso
from app.supabase_store import create_supabase_client, upsert_ads
from app.sync_service import configure_logging


def main() -> int:
    configure_logging()

    if len(sys.argv) < 2:
        print(
            "Uso: python main_csv.py <archivo.csv|archivo.json>\n"
            "\n"
            "Ejemplo:\n"
            "  python main_csv.py data/ads_siglo21.csv\n"
            "  python main_csv.py data/ads_export.json\n"
            "\n"
            "Ver app/csv_client.py para el formato esperado del archivo.",
            file=sys.stderr,
        )
        return 1

    file_path = sys.argv[1]
    settings = load_settings()
    supabase = create_supabase_client(settings)
    now_iso = utc_now_iso()

    rows: list[dict] = []
    try:
        for raw in iter_ads_from_csv(file_path):
            row = normalize_ad_row(raw, now_iso=now_iso)
            if not row["ad_id"] or not row["page_id"]:
                continue
            rows.append(row)
    except CsvImportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print("No se encontraron anuncios válidos en el archivo.")
        return 0

    chunk_errors = upsert_ads(supabase, rows)

    print("-- Importacion completada --")
    print(f"  Archivo            : {file_path}")
    print(f"  Ads importados     : {len(rows)}")
    print(f"  Errores de chunk   : {chunk_errors}")
    if chunk_errors:
        print("  WARN: Algunos chunks fallaron. Revisa los logs para mas detalle.")

    return 1 if chunk_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
