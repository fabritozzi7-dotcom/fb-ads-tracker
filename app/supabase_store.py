from __future__ import annotations

import logging
from typing import Any

from supabase import Client, create_client

from app.config import Settings

logger = logging.getLogger(__name__)

_UPSERT_CHUNK = 300


def create_supabase_client(settings: Settings) -> Client:
    return create_client(settings.supabase_url, settings.supabase_key)


def upsert_ads(client: Client, rows: list[dict[str, Any]]) -> tuple[int, int]:
    """Upserta filas en chunks. Devuelve (upserted, errores)."""
    if not rows:
        return 0, 0
    errors = 0
    upserted = 0
    for i in range(0, len(rows), _UPSERT_CHUNK):
        chunk = rows[i : i + _UPSERT_CHUNK]
        try:
            client.table("anuncios_competencia").upsert(
                chunk,
                on_conflict="ad_id",
            ).execute()
            upserted += len(chunk)
        except Exception:
            errors += 1
            logger.exception(
                "Error en upsert del chunk %s-%s (%s filas)",
                i,
                i + len(chunk),
                len(chunk),
            )
    return upserted, errors
