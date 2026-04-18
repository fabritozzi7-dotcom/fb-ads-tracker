from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_key: str
    facebook_access_token: str
    graph_version: str = "v19.0"
    mark_stale_inactive: bool = True
    meta_max_retries: int = 5
    meta_initial_backoff_seconds: float = 2.0


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Falta la variable de entorno obligatoria: {name}")
    return value


def load_settings() -> Settings:
    return Settings(
        supabase_url=_require_env("SUPABASE_URL"),
        supabase_key=_require_env("SUPABASE_KEY"),
        facebook_access_token=_require_env("FACEBOOK_ACCESS_TOKEN"),
        graph_version=os.getenv("META_GRAPH_VERSION", "v19.0").strip() or "v19.0",
        mark_stale_inactive=os.getenv("MARK_STALE_INACTIVE", "true").lower()
        in ("1", "true", "yes", "y"),
        meta_max_retries=int(os.getenv("META_MAX_RETRIES", "5")),
        meta_initial_backoff_seconds=float(
            os.getenv("META_INITIAL_BACKOFF_SECONDS", "2.0")
        ),
    )


def parse_page_ids_from_env() -> list[str] | None:
    raw = os.getenv("SEARCH_PAGE_IDS", "").strip()
    if not raw:
        return None
    return [p.strip() for p in raw.split(",") if p.strip()]
