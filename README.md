# FB Ads Tracker

Pipeline ETL que sincroniza anuncios activos de competidores desde la **Meta Ads Library API** hacia una tabla en **Supabase** (Postgres). Orientado al mercado argentino de educación superior.

## Arquitectura

```
.env (configuración)
  │
  ▼
config.py ── carga y valida variables de entorno
  │
  ▼
meta_archive_client.py ── EXTRACT: consulta Graph API con paginación y retry
  │
  ▼
normalize.py ── TRANSFORM: mapea campos de la API → columnas de la tabla
  │
  ▼
supabase_store.py ── LOAD: upsert en chunks a tabla anuncios_competencia
  │
  ▼
sync_service.py ── orquesta el flujo completo + detección de ads inactivos
  │
  ▼
main.py ── punto de entrada CLI, imprime resumen
```

### Tabla `anuncios_competencia`

| Columna       | Tipo      | Descripción                              |
|---------------|-----------|------------------------------------------|
| `ad_id`       | text (PK) | ID único del anuncio en Meta             |
| `page_id`     | text      | ID de la página que publicó el anuncio   |
| `page_name`   | text      | Nombre de la página                      |
| `ad_text`     | text      | Texto creativo del anuncio               |
| `snapshot_url` | text     | URL al snapshot del anuncio en Meta      |
| `image_url`   | text      | URL de la imagen/thumbnail (si disponible) |
| `start_date`  | date      | Fecha de inicio de entrega               |
| `last_seen`   | timestamp | Última vez que la API devolvió el anuncio |
| `is_active`   | boolean   | Si el anuncio sigue activo               |

## Requisitos

- Python 3.10+
- Cuenta en [Supabase](https://supabase.com) con la tabla `anuncios_competencia` creada
- Token de acceso de Meta con permiso `ads_read`

## Instalación

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd fb-ads-tracker

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Copiá `.env.example` a `.env` y completá los valores:

```bash
cp .env.example .env
```

Variables obligatorias:

| Variable                 | Descripción                                  |
|--------------------------|----------------------------------------------|
| `SUPABASE_URL`           | URL de tu proyecto Supabase                  |
| `SUPABASE_KEY`           | API key (anon o service_role)                |
| `FACEBOOK_ACCESS_TOKEN`  | Token de acceso con permiso `ads_read`       |

Variables opcionales:

| Variable                       | Default | Descripción                                    |
|--------------------------------|---------|------------------------------------------------|
| `SEARCH_PAGE_IDS`              | —       | IDs de páginas separados por coma              |
| `META_GRAPH_VERSION`           | v19.0   | Versión de la Graph API                        |
| `MARK_STALE_INACTIVE`          | true    | Marcar inactivos los ads que desaparecen       |
| `META_MAX_RETRIES`             | 5       | Reintentos ante rate-limiting                  |
| `META_INITIAL_BACKOFF_SECONDS` | 2.0     | Backoff inicial en segundos                    |

## Uso

```bash
python main.py
```

El script consulta la API, inserta/actualiza anuncios en Supabase y marca como inactivos los que ya no aparecen.

## Ejecución automática (GitHub Actions)

El workflow `.github/workflows/sync.yml` ejecuta la sincronización diariamente a las 6:00 AM UTC.

### Configurar secrets en GitHub

1. Ir a **Settings → Secrets and variables → Actions** en tu repositorio
2. Agregar los siguientes **Repository secrets**:

| Secret                   | Valor                              |
|--------------------------|------------------------------------|
| `SUPABASE_URL`           | URL de tu proyecto Supabase        |
| `SUPABASE_KEY`           | API key de Supabase                |
| `FACEBOOK_ACCESS_TOKEN`  | Token de acceso de Meta            |
| `SEARCH_PAGE_IDS`        | IDs de páginas separados por coma  |

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```
