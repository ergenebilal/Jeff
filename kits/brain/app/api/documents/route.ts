import { NextRequest, NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";
import { ingestDocument, chunkText } from "@/lib/rag";

/**
 * GET /api/documents
 * Returns all documents with their source info.
 */
export async function GET() {
  const { data, error } = await supabaseAdmin
    .from("documents")
    .select(`
      id,
      title,
      path,
      owner,
      status,
      views,
      freshness,
      snippet,
      created_at,
      source_id,
      sources!inner(name, type)
    `)
    .order("created_at", { ascending: false });

  if (error) {
    console.error("Failed to fetch documents:", error);
    return NextResponse.json({ documents: [] });
  }

  return NextResponse.json({ documents: data || [] });
}

/**
 * POST /api/documents
 * Ingest a new document into the knowledge base.
 * Body: { title: string, content: string, sourceId?: string }
 */
export async function POST(req: NextRequest) {
  try {
    const { title, content, sourceId } = await req.json();

    if (!title || !content) {
      return NextResponse.json(
        { error: "title ve content gerekli." },
        { status: 400 },
      );
    }

    const docId = await ingestDocument(
      title,
      content,
      sourceId || "00000000-0000-0000-0000-000000000001",
    );

    if (!docId) {
      return NextResponse.json(
        { error: "Belge eklenirken bir hata oluştu." },
        { status: 500 },
      );
    }

    return NextResponse.json({ id: docId, title, status: "ingested" });
  } catch (err) {
    console.error("Document ingest error:", err);
    return NextResponse.json(
      { error: "Bir hata oluştu." },
      { status: 500 },
    );
  }
}
