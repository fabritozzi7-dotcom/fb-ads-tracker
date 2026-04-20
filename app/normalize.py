"""Transformación de datos crudos de Apify al esquema de anuncios_competencia.

Formato REAL de salida del Actor curious_coder/facebook-ads-library-scraper (v2.7):
{
    "ad_archive_id": "1016127757754699",   # ID único del Ad Library (siempre presente)
    "ad_id": null,                          # puede ser null
    "page_name": "Nombre de la Página",
    "page_id": "301506776559902",
    "start_date": 1776495600,               # Unix timestamp (segundos)
    "end_date": 1776582000,                 # Unix timestamp (segundos) o null
    "start_date_formatted": "2026-04-18 07:00:00",
    "end_date_formatted": "2026-04-19 07:00:00",
    "is_active": false,
    "snapshot": {
        "body": {"text": "Texto del anuncio..."},  # o null
        "caption": null,                            # a veces tiene valor
        "cta_text": "Más información",              # o null
        "link_url": "https://example.com/landing",  # o null
        "images": [{"original_image_url": "https://..."}],  # puede estar vacío
        "videos": [{"video_hd_url": "...", "video_sd_url": "..."}],
        "display_format": "VIDEO",
        "page_name": "Nombre",
        "byline": "Nombre"
    },
    "categories": ["POLITICAL"],
    "publisher_platform": ["FACEBOOK", "INSTAGRAM"],
    "spend": "ARS500K - ARS600K",
    "impressions_with_index": {"impressions_text": "700K - 800K"},
    "ad_library_url": "https://www.facebook.com/ads/library/?id=..."
}
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

_TEMPLATE_VAR_RE = re.compile(r"\{\{[^}]*\}\}")

# Palabras clave por competidor para filtrar anuncios legítimos.
# Solo se aceptan anuncios cuyo page_name contenga al menos una keyword.
COMPETIDOR_KEYWORDS: dict[str, list[str]] = {
    "Universidad Blas Pascal": ["blas pascal", "ubp", "red pascal"],
    "Universidad Católica de Córdoba": ["católica", "catol", "ucc", "icp córdoba", "icp cordoba"],
}


def is_page_legitimate(page_name: str | None, competidor: str) -> bool:
    """Verifica que el page_name pertenezca realmente al competidor."""
    if not page_name:
        return False
    keywords = COMPETIDOR_KEYWORDS.get(competidor)
    if not keywords:
        return True  # sin filtro configurado, aceptar todo
    name_lower = page_name.lower()
    return any(kw in name_lower for kw in keywords)


def normalize_ad(raw: dict[str, Any], competidor: str) -> dict[str, Any]:
    """Convierte un dict crudo de Apify al formato de la tabla anuncios_competencia."""

    ad_id = str(raw.get("ad_archive_id") or raw.get("ad_id") or "")
    if not ad_id:
        raise ValueError("El anuncio no tiene ad_archive_id ni ad_id")

    snapshot = raw.get("snapshot") or {}

    return {
        "ad_id": ad_id,
        "competidor": competidor,
        "page_name": raw.get("page_name"),
        "page_id": str(raw.get("page_id", "") or ""),
        "ad_text": _clean_template_vars(_extract_text(snapshot)),
        "image_url": _extract_image(snapshot),
        "video_url": _extract_video(snapshot),
        "landing_url": _clean_template_vars(snapshot.get("link_url")),
        "start_date": _ts_to_date(raw.get("start_date")),
        "end_date": _ts_to_date(raw.get("end_date")),
        "is_active": raw.get("is_active", True),
        "raw_data": raw,
        "updated_at": _utc_now_iso(),
    }


def _extract_text(snapshot: dict[str, Any]) -> str | None:
    """Extrae el texto del anuncio desde el snapshot.

    El campo 'body' puede ser un dict {"text": "..."} o un string directo.
    'caption' es un campo alternativo que a veces tiene valor.
    """
    body = snapshot.get("body")
    if isinstance(body, dict):
        text = body.get("text", "")
    elif isinstance(body, str):
        text = body
    else:
        text = ""
    text = text or snapshot.get("caption") or ""
    cta = snapshot.get("cta_text") or ""
    if cta and text:
        return f"{text}\n[CTA: {cta}]"
    return text or None


def _extract_image(snapshot: dict[str, Any]) -> str | None:
    """Extrae la primera URL de imagen disponible.

    Orden de prioridad:
    1. snapshot.images[0].original_image_url
    2. snapshot.cards[0].original_image_url / resized_image_url
    3. snapshot.videos[0].video_preview_image_url
    4. snapshot.extra_images[0] (si es string o dict)
    """
    # 1. images[] directo
    images = snapshot.get("images") or []
    if images and isinstance(images, list):
        img = images[0]
        if isinstance(img, dict):
            url = img.get("original_image_url") or img.get("url")
            if url:
                return url
        if isinstance(img, str) and img:
            return img

    # 2. cards[] (anuncios carousel/DCO)
    cards = snapshot.get("cards") or []
    if cards and isinstance(cards, list):
        card = cards[0]
        if isinstance(card, dict):
            url = card.get("original_image_url") or card.get("resized_image_url")
            if url:
                return url

    # 3. video preview image
    videos = snapshot.get("videos") or []
    if videos and isinstance(videos, list):
        vid = videos[0]
        if isinstance(vid, dict):
            url = vid.get("video_preview_image_url")
            if url:
                return url

    # 4. extra_images
    extra = snapshot.get("extra_images") or []
    if extra and isinstance(extra, list):
        ei = extra[0]
        if isinstance(ei, dict):
            url = ei.get("original_image_url") or ei.get("url")
            if url:
                return url
        if isinstance(ei, str) and ei:
            return ei

    return None


def _extract_video(snapshot: dict[str, Any]) -> str | None:
    """Extrae la primera URL de video disponible (prefiere HD)."""
    videos = snapshot.get("videos") or []
    if videos and isinstance(videos, list):
        vid = videos[0]
        if isinstance(vid, dict):
            return vid.get("video_hd_url") or vid.get("video_sd_url")
        if isinstance(vid, str):
            return vid
    return None


def _clean_template_vars(value: str | None) -> str | None:
    """Elimina {{variable}} de template de anuncios dinámicos (DCO).
    Devuelve None si el resultado queda vacío."""
    if not value:
        return None
    cleaned = _TEMPLATE_VAR_RE.sub("", value).strip()
    return cleaned or None


def _ts_to_date(ts: int | float | None) -> str | None:
    """Convierte Unix timestamp (segundos) a string YYYY-MM-DD."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
