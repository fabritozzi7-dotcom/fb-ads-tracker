"""Cliente Apify para extraer anuncios de Facebook Ads Library.

Usa el Actor: curious_coder/facebook-ads-library-scraper
Docs: https://apify.com/curious_coder/facebook-ads-library-scraper
"""

from __future__ import annotations

import logging
from typing import Any

from apify_client import ApifyClient

from app.config import Settings

logger = logging.getLogger(__name__)

# Mapeo competidor -> URL de Facebook Ads Library
# Para agregar competidores, añadir entradas aquí o pasar URLs custom.
COMPETIDORES: dict[str, str] = {
    "Universidad Blas Pascal": (
        "https://www.facebook.com/ads/library/"
        "?active_status=active&ad_type=all&country=AR"
        "&q=Universidad%20Blas%20Pascal"
    ),
    "Universidad Católica de Córdoba": (
        "https://www.facebook.com/ads/library/"
        "?active_status=active&ad_type=all&country=AR"
        "&q=Universidad%20Cat%C3%B3lica%20de%20C%C3%B3rdoba"
    ),
}


def fetch_ads_for_competitor(
    settings: Settings,
    competidor: str,
    url: str | None = None,
) -> list[dict[str, Any]]:
    """Ejecuta el Actor de Apify y devuelve la lista de anuncios crudos.

    Args:
        settings: Configuración con token y actor_id.
        competidor: Nombre del competidor (se usa para log y lookup en COMPETIDORES).
        url: URL custom de Facebook Ads Library. Si es None, se busca en COMPETIDORES.

    Returns:
        Lista de dicts con los datos crudos del Actor.
    """
    target_url = url or COMPETIDORES.get(competidor)
    if not target_url:
        logger.error("No hay URL configurada para competidor: %s", competidor)
        return []

    client = ApifyClient(settings.apify_token)

    run_input = {
        "urls": [{"url": target_url}],
        "maxItems": settings.max_items_per_competitor,
    }

    logger.info(
        "Ejecutando Actor %s para '%s' (max %d items)...",
        settings.apify_actor_id,
        competidor,
        settings.max_items_per_competitor,
    )

    run = client.actor(settings.apify_actor_id).call(run_input=run_input)

    dataset_id = run["defaultDatasetId"]
    items: list[dict[str, Any]] = list(
        client.dataset(dataset_id).iterate_items()
    )

    logger.info("Obtenidos %d anuncios para '%s'", len(items), competidor)
    return items
