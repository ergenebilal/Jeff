import { NextRequest, NextResponse } from "next/server";
import { ask } from "@/lib/rag";
import { supabaseAdmin } from "@/lib/supabase";

/**
 * POST /api/chat
 *
 * Body: { question: string }
 * Returns: { answer, citations, confidence }
 *
 * Ask Brain a question → RAG pipeline → cited answer.
 */
export async function POST(req: NextRequest) {
  try {
    const { question } = await req.json();

    if (!question || typeof question !== "string" || question.trim().length === 0) {
      return NextResponse.json(
        { error: "Lütfen bir soru girin." },
        { status: 400 },
      );
    }

    const result = await ask(question.trim());

    return NextResponse.json(result);
  } catch (err) {
    console.error("Chat API error:", err);
    return NextResponse.json(
      { error: "Bir hata oluştu. Lütfen daha sonra tekrar deneyin.", answer: "", citations: [], confidence: 0 },
      { status: 500 },
    );
  }
}

/**
 * GET /api/chat?q=...
 * Simpler query-string interface for quick questions.
 */
export async function GET(req: NextRequest) {
  const question = req.nextUrl.searchParams.get("q");
  if (!question) {
    return NextResponse.json({ error: "?q parametresi gerekli." }, { status: 400 });
  }
  return POST(new NextRequest(req.url, {
    method: "POST",
    body: JSON.stringify({ question }),
    headers: { "content-type": "application/json" },
  }));
}
