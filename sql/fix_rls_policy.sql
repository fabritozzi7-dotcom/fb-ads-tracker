-- =============================================================
-- FIX: Agregar policy de lectura pública para anuncios_competencia
-- Ejecutar en Supabase SQL Editor para que el dashboard web
-- pueda leer los datos con la anon key.
-- =============================================================

-- Asegurar que RLS está habilitado
ALTER TABLE anuncios_competencia ENABLE ROW LEVEL SECURITY;

-- Permitir lectura pública (los datos de Meta Ads Library son públicos)
CREATE POLICY "Allow public read access"
ON anuncios_competencia
FOR SELECT
USING (true);
