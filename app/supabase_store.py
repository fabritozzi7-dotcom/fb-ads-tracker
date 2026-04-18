from __future__ import annotations

import logging
from typing import Any

from supabase import Client, create_client

from app.config import Settings

logger = logging.getLogger(__name__)

_UPSERT_CHUNK = 300
_INACTIVE_CHUNK = 150


def create_supabase_client(settings: Settings) -> Client:
    return create_client(settings.supabase_url, settings.supabase_key)


def upsert_ads(client: Client, rows: list[dict[str, Any]]) -> int:
    """Upserta filas en chunks. Devuelve la cantidad de errores de chunk."""
    if not rows:
        return 0
    errors = 0
    for i in range(0, len(rows), _UPSERT_CHUNK):
        chunk = rows[i : i + _UPSERT_CHUNK]
        try:
            client.table("anuncios_competencia").upsert(
                chunk,
                on_conflict="ad_id",
            ).execute()
        except Exception:
            errors += 1
            logger.exception(
                "Error en upsert del chunk %s-%s (%s filas)",
                i,
                i + len(chunk),
                len(chunk),
            )
    return errors


def fetch_active_ad_ids_for_pages(
    client: Client, page_ids: list[str]
) -> dict[str, set[str]]:
    """page_id -> conjunto de ad_id marcados activos en BD."""
    result: dict[str, set[str]] = {str(p): set() for p in page_ids}
    if not page_ids:
        return result

    page_id_list = [str(p) for p in page_ids]
    page_size = 1000
    start = 0
    while True:
        end = start + page_size - 1
        resp = (
            client.table("anuncios_competencia")
            .select("ad_id,page_id")
            .in_("page_id", page_id_list)
            .eq("is_active", True)
            .range(start, end)
            .execute()
        )
        batch = resp.data or []
        for row in batch:
            pid = str(row.get("page_id") or "")
            aid = str(row.get("ad_id") or "")
            if pid in result and aid:
                result[pid].add(aid)
        if len(batch) < page_size:
            break
        start += page_size

    return result


def mark_ads_inactive(client: Client, ad_ids: list[str]) -> None:
    if not ad_ids:
        return
    for i in range(0, len(ad_ids), _INACTIVE_CHUNK):
        part = ad_ids[i : i + _INACTIVE_CHUNK]
        client.table("anuncios_competencia").update({"is_active": False}).in_(
            "ad_id", part
        ).execute()
