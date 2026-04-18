"""
Cliente para importar anuncios desde un archivo CSV local exportado
de la Meta Ad Library (https://www.facebook.com/ads/library/).

Uso:
  1. Ir a facebook.com/ads/library
  2. Buscar la página competidora (ej: "Universidad Siglo 21")
  3. Exportar/copiar los datos de los anuncios activos
  4. Guardar como CSV con las columnas esperadas (ver EXPECTED_COLUMNS)
  5. Correr main_csv.py --csv ruta/al/archivo.csv

El CSV también puede generarse manualmente con datos copiados de la
Ad Library web. El formato mínimo requerido es:

  ad_id,page_id,page_name,ad_text,snapshot_url,start_date
  123456,789,"Mi Página","Texto del anuncio","https://...",2024-01-15

Columnas opcionales: image_url, link_caption, link_title
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = {
    "ad_id",
    "page_id",
    "page_name",
    "ad_text",
    "snapshot_url",
    "start_date",
}

OPTIONAL_COLUMNS = {
    "image_url",
    "link_caption",
    "link_title",
}


class CsvImportError(RuntimeError):
    pass


def _detect_delimiter(first_line: str) -> str:
    """Detecta si el CSV usa coma, punto y coma, o tab como separador."""
    for delim in [",", ";", "\t"]:
        if delim in first_line:
            return delim
    return ","


def iter_ads_from_csv(file_path: str | Path) -> Iterator[dict[str, Any]]:
    """Lee un CSV local y devuelve dicts compatibles con normalize_ad_row.

    Cada dict tiene las mismas claves que devuelve la Meta Graph API
    (id, page_id, page_name, ad_creative_bodies, ad_snapshot_url,
    ad_delivery_start_time) para que normalize.py funcione sin cambios.
    """
    path = Path(file_path)
    if not path.exists():
        raise CsvImportError(f"Archivo no encontrado: {path}")

    if path.suffix.lower() == ".json":
        yield from _iter_from_json(path)
        return

    text = path.read_text(encoding="utf-8-sig")  # soporta BOM de Excel
    lines = text.splitlines()
    if not lines:
        raise CsvImportError(f"Archivo vacío: {path}")

    delimiter = _detect_delimiter(lines[0])
    reader = csv.DictReader(lines, delimiter=delimiter)

    if reader.fieldnames is None:
        raise CsvImportError(f"No se pudieron leer las columnas de {path}")

    fields = {f.strip().lower() for f in reader.fieldnames}
    missing = EXPECTED_COLUMNS - fields
    if missing:
        raise CsvImportError(
            f"Faltan columnas obligatorias en el CSV: {', '.join(sorted(missing))}. "
            f"Columnas encontradas: {', '.join(sorted(fields))}"
        )

    count = 0
    for row in reader:
        # Normalizar keys a lowercase y strip
        clean = {k.strip().lower(): (v or "").strip() for k, v in row.items()}

        # Convertir al formato de la Graph API para que normalize_ad_row
        # funcione sin cambios
        api_format: dict[str, Any] = {
            "id": clean.get("ad_id", ""),
            "page_id": clean.get("page_id", ""),
            "page_name": clean.get("page_name", ""),
            "ad_creative_bodies": [clean["ad_text"]] if clean.get("ad_text") else None,
            "ad_snapshot_url": clean.get("snapshot_url", ""),
            "ad_delivery_start_time": clean.get("start_date", ""),
            "ad_creative_link_captions": (
                [clean["link_caption"]] if clean.get("link_caption") else None
            ),
            "ad_creative_link_titles": (
                [clean["link_title"]] if clean.get("link_title") else None
            ),
        }
        count += 1
        yield api_format

    logger.info("CSV procesado: %s filas leídas de %s", count, path)


def _iter_from_json(path: Path) -> Iterator[dict[str, Any]]:
    """Lee un archivo JSON con una lista de anuncios en formato API."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CsvImportError(f"Error leyendo JSON {path}: {exc}") from exc

    if isinstance(data, dict) and "data" in data:
        items = data["data"]
    elif isinstance(data, list):
        items = data
    else:
        raise CsvImportError(
            f"Formato JSON no reconocido en {path}: "
            "se espera una lista o un dict con clave 'data'"
        )

    for item in items:
        yield item

    logger.info("JSON procesado: %s anuncios leídos de %s", len(items), path)
