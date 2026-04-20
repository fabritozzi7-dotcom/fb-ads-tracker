"""Análisis de anuncios con Google Gemini AI.

Lee anuncios sin analizar de Supabase, los envía a Gemini para
obtener un análisis estructurado, y guarda el resultado en ai_analysis.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv
from supabase import Client

from app.config import load_settings
from app.supabase_store import create_supabase_client

load_dotenv()

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """\
Analizá este anuncio de educación superior argentina y respondé \
SOLO con un JSON válido (sin markdown, sin ```json, solo el JSON) \
con esta estructura exacta:
{{
  "tono": "emocional|racional|urgente|aspiracional|informativo",
  "cta": "el call to action principal en 5 palabras o menos",
  "publico_objetivo": "descripción del público en 10 palabras",
  "propuesta_valor": "qué promete el anuncio en 10 palabras",
  "formato_recomendado": "imagen|video|carrusel",
  "score_claridad": número del 1 al 10,
  "score_urgencia": número del 1 al 10,
  "palabras_clave": ["array", "de", "hasta", "5", "palabras"],
  "resumen": "síntesis del anuncio en una oración"
}}

Anuncio del competidor: {competidor}
Página: {page_name}
Texto del anuncio:
{ad_text}
"""

BATCH_SIZE = 10
DELAY_BETWEEN_CALLS = 1.0  # segundos


def _init_gemini() -> genai.GenerativeModel:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Falta la variable de entorno GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    return genai.GenerativeModel(model_name)


def _fetch_unanalyzed(db: Client, limit: int | None = None) -> list[dict[str, Any]]:
    """Trae anuncios con ad_text que no tienen ai_analysis."""
    query = (
        db.table("anuncios_competencia")
        .select("id,ad_id,competidor,page_name,ad_text")
        .not_.is_("ad_text", "null")
        .is_("ai_analysis", "null")
        .order("created_at")
    )
    if limit:
        query = query.limit(limit)
    resp = query.execute()
    return resp.data or []


def _parse_json_response(text: str) -> dict[str, Any]:
    """Extrae JSON de la respuesta de Gemini, limpiando markdown si viene."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove ```json ... ```
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


def _analyze_single(
    model: genai.GenerativeModel, ad: dict[str, Any]
) -> dict[str, Any] | None:
    """Analiza un anuncio con Gemini. Devuelve el JSON o None si falla."""
    prompt = ANALYSIS_PROMPT.format(
        competidor=ad.get("competidor", ""),
        page_name=ad.get("page_name", ""),
        ad_text=ad.get("ad_text", ""),
    )
    try:
        response = model.generate_content(prompt)
        return _parse_json_response(response.text)
    except Exception as e:
        logger.warning("Error analizando ad %s: %s", ad.get("ad_id"), e)
        return None


def _save_analysis(db: Client, ad_id: str, analysis: dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    db.table("anuncios_competencia").update(
        {"ai_analysis": analysis, "ai_analyzed_at": now}
    ).eq("id", ad_id).execute()


def run_analysis(limit: int | None = None, dry_run: bool = False) -> dict[str, int]:
    """Ejecuta el análisis en batch.

    Args:
        limit: Máximo de anuncios a analizar (None = todos).
        dry_run: Si True, solo imprime sin guardar.

    Returns:
        Dict con contadores: analyzed, errors, skipped.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = load_settings()
    db = create_supabase_client(settings)
    model = _init_gemini()

    ads = _fetch_unanalyzed(db, limit)
    total = len(ads)
    print(f"\nAnuncios pendientes de análisis: {total}")

    if total == 0:
        print("No hay anuncios para analizar.")
        return {"analyzed": 0, "errors": 0, "skipped": 0}

    analyzed = 0
    errors = 0
    start_time = time.time()

    for i, ad in enumerate(ads, 1):
        ad_text = ad.get("ad_text", "")
        if not ad_text or len(ad_text.strip()) < 10:
            print(f"  [{i}/{total}] Saltando {ad['ad_id']} (texto muy corto)")
            continue

        print(f"  [{i}/{total}] Analizando {ad['ad_id']}...", end=" ")

        result = _analyze_single(model, ad)

        if result:
            if dry_run:
                print("OK (dry run)")
                print(f"    {json.dumps(result, ensure_ascii=False)[:120]}...")
            else:
                _save_analysis(db, ad["id"], result)
                print("OK")
            analyzed += 1
        else:
            print("ERROR")
            errors += 1

        # Rate limit: delay between calls, pause extra every BATCH_SIZE
        if i < total:
            time.sleep(DELAY_BETWEEN_CALLS)
            if i % BATCH_SIZE == 0:
                print(f"  --- Pausa entre batches ({i}/{total}) ---")
                time.sleep(2.0)

    elapsed = time.time() - start_time
    skipped = total - analyzed - errors

    print(f"\n{'=' * 50}")
    print(f"  Analizados:  {analyzed}")
    print(f"  Errores:     {errors}")
    print(f"  Saltados:    {skipped}")
    print(f"  Tiempo:      {elapsed:.1f}s")
    print(f"{'=' * 50}\n")

    return {"analyzed": analyzed, "errors": errors, "skipped": skipped}


if __name__ == "__main__":
    import sys

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_analysis(limit=limit)
