import { supabase } from "@/lib/supabase";

export async function GET() {
  const { data, error } = await supabase
    .from("anuncios_competencia")
    .select("competidor, ai_analysis")
    .not("ai_analysis", "is", null);

  if (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }

  const ads = data || [];

  // Aggregate by competitor
  const competitors = new Map<
    string,
    {
      tonos: Record<string, number>;
      ctas: Record<string, number>;
      keywords: Record<string, number>;
      totalClaridad: number;
      totalUrgencia: number;
      count: number;
    }
  >();

  for (const ad of ads) {
    const ai = ad.ai_analysis as Record<string, unknown>;
    if (!ai) continue;
    const comp = ad.competidor as string;

    if (!competitors.has(comp)) {
      competitors.set(comp, {
        tonos: {},
        ctas: {},
        keywords: {},
        totalClaridad: 0,
        totalUrgencia: 0,
        count: 0,
      });
    }

    const stats = competitors.get(comp)!;
    stats.count++;

    // Tonos
    const tono = (ai.tono as string) || "desconocido";
    stats.tonos[tono] = (stats.tonos[tono] || 0) + 1;

    // CTAs
    const cta = (ai.cta as string) || "";
    if (cta) {
      const ctaNorm = cta.toLowerCase();
      stats.ctas[ctaNorm] = (stats.ctas[ctaNorm] || 0) + 1;
    }

    // Keywords
    const kws = (ai.palabras_clave as string[]) || [];
    for (const kw of kws) {
      const kwNorm = kw.toLowerCase();
      stats.keywords[kwNorm] = (stats.keywords[kwNorm] || 0) + 1;
    }

    // Scores
    stats.totalClaridad += (ai.score_claridad as number) || 0;
    stats.totalUrgencia += (ai.score_urgencia as number) || 0;
  }

  const insights: Record<
    string,
    {
      tonos: Record<string, number>;
      topCtas: [string, number][];
      topKeywords: [string, number][];
      avgClaridad: number;
      avgUrgencia: number;
      count: number;
    }
  > = {};

  for (const [comp, stats] of competitors) {
    insights[comp] = {
      tonos: stats.tonos,
      topCtas: Object.entries(stats.ctas)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5),
      topKeywords: Object.entries(stats.keywords)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15),
      avgClaridad: stats.count ? +(stats.totalClaridad / stats.count).toFixed(1) : 0,
      avgUrgencia: stats.count ? +(stats.totalUrgencia / stats.count).toFixed(1) : 0,
      count: stats.count,
    };
  }

  // Global keywords
  const globalKw: Record<string, number> = {};
  for (const stats of competitors.values()) {
    for (const [kw, c] of Object.entries(stats.keywords)) {
      globalKw[kw] = (globalKw[kw] || 0) + c;
    }
  }

  return Response.json({
    insights,
    globalKeywords: Object.entries(globalKw)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20),
    totalAnalyzed: ads.length,
  });
}
