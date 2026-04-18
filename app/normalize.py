from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any


def _join_creative_bodies(bodies: Any) -> str | None:
    if bodies is None:
        return None
    if isinstance(bodies, list):
        parts = [str(b).strip() for b in bodies if str(b).strip()]
        if not parts:
            return None
        return "\n".join(parts)
    return str(bodies).strip() or None


def _parse_start_date(value: Any) -> str | None:
    """Devuelve YYYY-MM-DD o None para columnas tipo date en Postgres."""
    if not value:
        return None
    s = str(value).strip()
    if not s:
        return None
    if "T" in s:
        s = s.split("T", 1)[0]
    try:
        return str(date.fromisoformat(s[:10]))
    except ValueError:
        return None


def _first_non_empty(values: Any) -> str | None:
    """Devuelve el primer elemento no vacío de una lista, o None."""
    if not isinstance(values, list):
        return None
    for v in values:
        s = str(v).strip()
        if s:
            return s
    return None


def normalize_ad_row(raw: dict[str, Any], *, now_iso: str) -> dict[str, Any]:
    """Mapea un elemento de la API a columnas de `anuncios_competencia` (sin `id`)."""
    ad_id = str(raw.get("id") or "").strip()
    page_id = str(raw.get("page_id") or "").strip()
    page_name = str(raw.get("page_name") or "").strip() or None

    # La Meta Ads Library API no expone una URL directa de imagen/thumbnail
    # en el endpoint ads_archive. El campo ad_snapshot_url apunta a una
    # preview interactiva completa del anuncio (que incluye la imagen).
    # Si en el futuro Meta agrega un campo de imagen, mapearlo acá.
    snapshot_url = raw.get("ad_snapshot_url")

    return {
        "ad_id": ad_id,
        "page_id": page_id,
        "page_name": page_name,
        "ad_text": _join_creative_bodies(raw.get("ad_creative_bodies")),
        "snapshot_url": snapshot_url,
        "image_url": None,
        "link_caption": _first_non_empty(raw.get("ad_creative_link_captions")),
        "link_title": _first_non_empty(raw.get("ad_creative_link_titles")),
        "start_date": _parse_start_date(raw.get("ad_delivery_start_time")),
        "last_seen": now_iso,
        "is_active": True,
    }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
