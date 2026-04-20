"""Entry point: extrae anuncios de competidores vía Apify y los guarda en Supabase."""

from __future__ import annotations

import logging
import sys

from app.apify_client import COMPETIDORES, fetch_ads_for_competitor
from app.config import load_settings
from app.normalize import is_page_legitimate, normalize_ad
from app.supabase_store import create_supabase_client, upsert_ads


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    settings = load_settings()
    db = create_supabase_client(settings)

    total_errors = 0
    print("\n" + "=" * 60)
    print("  FB Ads Tracker — Apify Pipeline")
    print("=" * 60)

    for competidor in COMPETIDORES:
        print(f"\n--- {competidor} ---")

        raw_ads = fetch_ads_for_competitor(settings, competidor)
        if not raw_ads:
            print(f"  Sin resultados para {competidor}")
            continue

        rows = []
        normalize_errors = 0
        filtered_out = 0
        for ad in raw_ads:
            try:
                page_name = ad.get("page_name") or (ad.get("snapshot") or {}).get("page_name")
                if not is_page_legitimate(page_name, competidor):
                    filtered_out += 1
                    continue
                rows.append(normalize_ad(ad, competidor))
            except Exception as e:
                normalize_errors += 1
                logger.warning("Error normalizando anuncio: %s", e)

        upserted, db_errors = upsert_ads(db, rows)
        total_errors += db_errors + normalize_errors

        print(f"  Anuncios obtenidos:      {len(raw_ads)}")
        print(f"  Filtrados (no legítimos):{filtered_out}")
        print(f"  Normalizados OK:         {len(rows)}")
        print(f"  Upserted en Supabase:    {upserted}")
        if normalize_errors:
            print(f"  Errores normalización:   {normalize_errors}")
        if db_errors:
            print(f"  Errores DB (chunks):     {db_errors}")

    print("\n" + "=" * 60)
    if total_errors:
        print(f"  Finalizado con {total_errors} error(es)")
    else:
        print("  Finalizado sin errores")
    print("=" * 60 + "\n")

    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
