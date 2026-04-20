import { supabase } from "@/lib/supabase";
import type { NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;

  const competidor = searchParams.get("competidor");
  const estado = searchParams.get("estado");
  const busqueda = searchParams.get("busqueda");
  const page = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = 20;

  let query = supabase
    .from("anuncios_competencia")
    .select("*", { count: "exact" })
    .order("start_date", { ascending: false })
    .range((page - 1) * pageSize, page * pageSize - 1);

  if (competidor && competidor !== "todos") {
    query = query.eq("competidor", competidor);
  }
  if (estado === "activo") {
    query = query.eq("is_active", true);
  } else if (estado === "inactivo") {
    query = query.eq("is_active", false);
  }
  if (busqueda) {
    query = query.ilike("ad_text", `%${busqueda}%`);
  }

  const { data, error, count } = await query;

  if (error) {
    console.error("Supabase query error:", error);
    return Response.json(
      { error: error.message, code: error.code, details: error.details },
      { status: 500 }
    );
  }

  return Response.json({
    ads: data,
    total: count,
    page,
    pageSize,
    totalPages: Math.ceil((count || 0) / pageSize),
  });
}
