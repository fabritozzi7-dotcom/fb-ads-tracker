from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_key: str
    apify_token: str
    apify_actor_id: str = "curious_coder/facebook-ads-library-scraper"
    max_items_per_competitor: int = 200


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Falta la variable de entorno obligatoria: {name}")
    return value


def load_settings() -> Settings:
    return Settings(
        supabase_url=_require_env("SUPABASE_URL"),
        supabase_key=_require_env("SUPABASE_KEY"),
        apify_token=_require_env("APIFY_TOKEN"),
        apify_actor_id=os.getenv(
            "APIFY_ACTOR_ID", "curious_coder/facebook-ads-library-scraper"
        ).strip(),
        max_items_per_competitor=int(
            os.getenv("APIFY_MAX_ITEMS", "200")
        ),
    )
