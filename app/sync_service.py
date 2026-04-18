from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from app.config import Settings, load_settings, parse_page_ids_from_env
from app.meta_archive_client import MetaArchiveError, iter_ads_archive
from app.normalize import normalize_ad_row, utc_now_iso
from app.supabase_store import (
    create_supabase_client,
    fetch_active_ad_ids_for_pages,
    mark_ads_inactive,
    upsert_ads,
)

logger = logging.getLogger(__name__)

def sync_competitor_ads(
    *,
    settings: Settings | None = None,
    search_page_ids: list[str] | None = None,
) -> dict[str, Any]:
    settings = settings or load_settings()
    page_ids = search_page_ids or parse_page_ids_from_env()
    if not page_ids:
        raise ValueError(
            "search_page_ids vacío: definí SEARCH_PAGE_IDS en .env "
            "(IDs de páginas separados por coma)"
        )

    now_iso = utc_now_iso()
    supabase = create_supabase_client(settings)

    seen_by_page: dict[str, set[str]] = defaultdict(set)
    buffer: list[dict[str, Any]] = []
    upserted = 0
    chunk_errors = 0
    flush_every = 400

    try:
        for raw in iter_ads_archive(settings, page_ids):
            row = normalize_ad_row(raw, now_iso=now_iso)
            if not row["ad_id"] or not row["page_id"]:
                continue
            buffer.append(row)
            seen_by_page[str(row["page_id"])].add(str(row["ad_id"]))
            if len(buffer) >= flush_every:
                chunk_errors += upsert_ads(supabase, buffer)
                upserted += len(buffer)
                buffer.clear()
    except MetaArchiveError:
        logger.exception("Error consultando Meta Ads Archive")
        raise

    if buffer:
        chunk_errors += upsert_ads(supabase, buffer)
        upserted += len(buffer)

    stale: list[str] = []
    if settings.mark_stale_inactive:
        previous = fetch_active_ad_ids_for_pages(supabase, page_ids)
        for pid in page_ids:
            pid_s = str(pid)
            prev_ids = previous.get(pid_s, set())
            still = seen_by_page.get(pid_s, set())
            stale.extend(sorted(prev_ids - still))

        if stale:
            mark_ads_inactive(supabase, stale)
            logger.info("Marcados inactivos (no devueltos por la API): %s", len(stale))

    return {
        "page_ids": page_ids,
        "upserted": upserted,
        "marked_inactive": len(stale),
        "chunk_errors": chunk_errors,
    }


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
