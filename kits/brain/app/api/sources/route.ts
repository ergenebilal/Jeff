import { NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

/**
 * GET /api/sources
 * Returns all connected sources with document counts.
 */
export async function GET() {
  const { data, error } = await supabaseAdmin
    .from("sources")
    .select(`
      id,
      name,
      type,
      connected,
      created_at,
      documents:documents(count)
    `)
    .order("created_at", { ascending: false });

  if (error) {
    console.error("Failed to fetch sources:", error);
    return NextResponse.json({ sources: [] });
  }

  return NextResponse.json({ sources: data || [] });
}
