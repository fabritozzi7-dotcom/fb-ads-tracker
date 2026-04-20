-- =============================================================
-- Schema para fb-ads-tracker (Apify pipeline)
-- Ejecutar en Supabase SQL Editor: https://supabase.com/dashboard
--   -> tu proyecto -> SQL Editor -> New Query -> pegar y Run
-- =============================================================

-- Eliminar tabla anterior si existe (cuidado: borra datos previos)
-- DROP TABLE IF EXISTS anuncios_competencia;

CREATE TABLE anuncios_competencia (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ad_id TEXT NOT NULL UNIQUE,
    competidor TEXT NOT NULL,
    page_name TEXT,
    page_id TEXT,
    ad_text TEXT,
    image_url TEXT,
    video_url TEXT,
    landing_url TEXT,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_competidor ON anuncios_competencia(competidor);
CREATE INDEX idx_is_active ON anuncios_competencia(is_active);
CREATE INDEX idx_start_date ON anuncios_competencia(start_date);

-- RLS: permitir lectura pública (los datos de ads son públicos)
ALTER TABLE anuncios_competencia ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access"
ON anuncios_competencia
FOR SELECT
USING (true);
