import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error(
    "Missing Supabase env vars:",
    JSON.stringify({
      hasUrl: !!supabaseUrl,
      hasKey: !!supabaseAnonKey,
    })
  );
}

export const supabase = createClient(supabaseUrl ?? "", supabaseAnonKey ?? "");

export interface AiAnalysis {
  tono: string;
  cta: string;
  publico_objetivo: string;
  propuesta_valor: string;
  formato_recomendado: string;
  score_claridad: number;
  score_urgencia: number;
  palabras_clave: string[];
  resumen: string;
}

export interface Ad {
  id: string;
  ad_id: string;
  competidor: string;
  page_name: string | null;
  page_id: string | null;
  ad_text: string | null;
  image_url: string | null;
  video_url: string | null;
  landing_url: string | null;
  start_date: string | null;
  end_date: string | null;
  is_active: boolean;
  ai_analysis: AiAnalysis | null;
  ai_analyzed_at: string | null;
  created_at: string;
  updated_at: string;
}
