from __future__ import annotations

import json
import logging
import time
from typing import Any, Iterator

import requests

from app.config import Settings

logger = logging.getLogger(__name__)

META_GRAPH_BASE = "https://graph.facebook.com"

_RATE_LIMIT_CODES = {4, 17, 32, 613, 80000, 80003, 80004, 80014}
_RATE_LIMIT_SUBCODES = {2446079}


class MetaArchiveError(RuntimeError):
    pass


def _is_rate_limit_error(payload: dict[str, Any]) -> bool:
    err = payload.get("error") or {}
    code = err.get("code")
    subcode = err.get("error_subcode")
    if code in _RATE_LIMIT_CODES or subcode in _RATE_LIMIT_SUBCODES:
        return True
    msg = (err.get("message") or "").lower()
    return "request limit" in msg or "rate limit" in msg or "too many" in msg


def _request_json_with_retries(
    settings: Settings,
    session: requests.Session,
    *,
    method: str,
    url: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    backoff = settings.meta_initial_backoff_seconds
    last_exc: Exception | None = None

    for attempt in range(1, settings.meta_max_retries + 1):
        try:
            resp = session.request(method, url, params=params, timeout=60)
            if resp.status_code == 429:
                raise MetaArchiveError("HTTP 429 Too Many Requests")

            data = resp.json()
            if "error" in data:
                if _is_rate_limit_error(data) or resp.status_code in (429, 503):
                    raise MetaArchiveError(json.dumps(data["error"], ensure_ascii=False))
                raise MetaArchiveError(json.dumps(data["error"], ensure_ascii=False))

            if resp.status_code >= 400:
                raise MetaArchiveError(resp.text)

            return data
        except (requests.RequestException, MetaArchiveError) as exc:
            last_exc = exc
            if attempt >= settings.meta_max_retries:
                break
            logger.warning(
                "Reintento %s/%s contra Graph API: %s",
                attempt,
                settings.meta_max_retries,
                exc,
            )
            time.sleep(backoff)
            backoff = min(backoff * 2, 120.0)

    assert last_exc is not None
    raise MetaArchiveError(f"Falló la petición tras reintentos: {last_exc}")


def iter_ads_archive(
    settings: Settings,
    search_page_ids: list[str],
) -> Iterator[dict[str, Any]]:
    """Pagina toda la respuesta de ads_archive para los page_ids dados."""
    session = requests.Session()
    url = f"{META_GRAPH_BASE}/{settings.graph_version}/ads_archive"
    params: dict[str, Any] = {
        "access_token": settings.facebook_access_token,
        "search_page_ids": json.dumps([str(p) for p in search_page_ids]),
        "ad_reached_countries": json.dumps(["AR"]),
        "ad_type": "ALL",
        "ad_active_status": "ACTIVE",
        "fields": ",".join(
            [
                "id",
                "ad_creative_bodies",
                "ad_creative_link_captions",
                "ad_creative_link_titles",
                "ad_snapshot_url",
                "page_name",
                "page_id",
                "ad_delivery_start_time",
            ]
        ),
        "limit": 100,
    }

    next_url: str | None = None

    while True:
        if next_url:
            payload = _request_json_with_retries(
                settings, session, method="GET", url=next_url, params=None
            )
            next_url = None
        else:
            payload = _request_json_with_retries(
                settings, session, method="GET", url=url, params=params
            )

        for item in payload.get("data") or []:
            yield item

        paging = payload.get("paging") or {}
        if paging.get("next"):
            next_url = str(paging["next"])
            continue

        cursors = paging.get("cursors") or {}
        after = cursors.get("after")
        if after:
            params["after"] = str(after)
            continue

        return
