/**
 * ErgeneAI Brain — RAG (Retrieval-Augmented Generation) engine.
 *
 * Uses Supabase full-text search for retrieval and OpenCode Go API
 * (OpenAI-compatible) for answer generation.
 *
 * Architecture:
 *   Question → Full-text search (tsvector) → Top-K chunks → LLM → Answer + citations
 */
import { supabaseAdmin } from "./supabase";

/* ── Types ────────────────────────────────────────────────────────────────── */

export interface Citation {
  title: string;
  source: string;
  docId: string;
}

export interface RagResult {
  answer: string;
  citations: Citation[];
  confidence: number;
}

export interface SearchResult {
  id: string;
  content: string;
  document_id: string;
  doc_title: string;
  doc_source: string;
  rank: number;
}

/* ── Configuration ────────────────────────────────────────────────────────── */

const OPENAI_BASE_URL =
  process.env.OPENAI_BASE_URL || "https://opencode.ai/zen/go/v1";
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || "";
const CHAT_MODEL = "deepseek-v4-flash"; // fast & affordable
const MAX_CHUNKS = 5; // top-k chunks to retrieve
const MIN_CONFIDENCE = 0.35; // below this = no answer
const MAX_TOKENS = 2048;

/* ── Chunking ─────────────────────────────────────────────────────────────── */

/**
 * Split a large text into overlapping chunks of ~N characters.
 */
export function chunkText(text: string, chunkSize = 1200, overlap = 200): string[] {
  if (!text || text.length <= chunkSize) return [text];
  const chunks: string[] = [];
  let i = 0;
  while (i < text.length) {
    const end = Math.min(i + chunkSize, text.length);
    const chunk = text.slice(i, end);
    chunks.push(chunk);
    i += chunkSize - overlap;
  }
  return chunks;
}

/* ── Ingest ───────────────────────────────────────────────────────────────── */

/**
 * Ingest a document: store in DB, chunk it, and prepare for search.
 */
export async function ingestDocument(
  title: string,
  content: string,
  sourceId = "00000000-0000-0000-0000-000000000001",
  owner = "ErgeneAI",
): Promise<string | null> {
  if (!content) return null;

  // 1. Insert document
  const { data: doc, error: docErr } = await supabaseAdmin
    .from("documents")
    .insert({
      title,
      source_id: sourceId,
      content,
      owner,
      status: "ready",
      snippet: content.slice(0, 200),
    })
    .select("id")
    .single();

  if (docErr || !doc) {
    console.error("Failed to insert document:", docErr);
    return null;
  }

  // 2. Chunk and insert chunks
  const chunks = chunkText(content);
  const chunkRows = chunks.map((chunk) => ({
    document_id: doc.id,
    content: chunk,
    metadata: { title, chunk_index: chunks.indexOf(chunk) },
  }));

  const { error: chunkErr } = await supabaseAdmin
    .from("document_chunks")
    .insert(chunkRows);

  if (chunkErr) {
    console.error("Failed to insert chunks:", chunkErr);
    // Delete document if chunks failed
    await supabaseAdmin.from("documents").delete().eq("id", doc.id);
    return null;
  }

  return doc.id;
}

/* ── Search ───────────────────────────────────────────────────────────────── */

/**
 * Search document chunks using full-text search (tsvector).
 * Falls back to ILIKE if no tsquery matches.
 */
export async function searchChunks(query: string, limit = MAX_CHUNKS): Promise<SearchResult[]> {
  // Extract meaningful content words (skip stop words)
  const stopWords = new Set([
    "bir", "bu", "şu", "o", "ve", "veya", "ile", "için", "ama", "ancak",
    "gibi", "kadar", "sonra", "önce", "üzeri", "altı", "arası", "mi",
    "mu", "mü", "da", "de", "mı", "mi", "mu", "mü",
    "hangi", "ne", "nasıl", "neden", "niçin", "kim", "nerede",
    "ben", "sen", "o", "biz", "siz", "onlar", "burada", "orada",
    "çok", "az", "daha", "en", "her", "hiç", "tüm", "bazı",
  ]);

  const words = query
    .split(/\s+/)
    .filter((w) => w.length > 2 && !stopWords.has(w.toLowerCase()));

  if (words.length === 0) return [];

  // Fetch all chunks with document info
  const { data: allChunks, error: fetchError } = await supabaseAdmin
    .from("document_chunks")
    .select(`
      id,
      content,
      document_id,
      documents!inner(title, source_id)
    `);

  if (fetchError || !allChunks || allChunks.length === 0) {
    console.error("Chunk fetch failed:", fetchError);
    // Fallback: try tsvector RPC
    const tsquery = words.map((w) => w + ":*").join(" & ");
    const { data: tsResults } = await supabaseAdmin.rpc(
      "search_document_chunks",
      { query_text: query, ts_query_text: tsquery, max_results: limit },
    );
    if (tsResults?.length) {
      return tsResults.map((r: any) => ({
        id: r.id,
        content: r.content,
        document_id: r.document_id,
        doc_title: r.doc_title || "Untitled",
        doc_source: r.doc_source || "manual",
        rank: r.rank || 0,
      }));
    }
    return [];
  }

  // Score each chunk by how many query words it matches (OR logic + density ranking)
  type Scored = { chunk: any; score: number; matchedWords: Set<string> };
  const scored: Scored[] = allChunks.map((chunk: any) => {
    const lower = chunk.content?.toLowerCase() || "";
    const matchedWords = new Set<string>();
    for (const word of words) {
      if (lower.includes(word.toLowerCase())) {
        matchedWords.add(word);
      }
    }
    return { chunk, score: matchedWords.size, matchedWords };
  });

  // Filter: only chunks that match at least one content word
  const matched = scored
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);

  if (matched.length === 0) {
    // Fallback: try tsvector RPC
    const tsquery = words.map((w) => w + ":*").join(" & ");
    const { data: tsResults } = await supabaseAdmin.rpc(
      "search_document_chunks",
      { query_text: query, ts_query_text: tsquery, max_results: limit },
    );
    if (tsResults?.length) {
      return tsResults.map((r: any) => ({
        id: r.id,
        content: r.content,
        document_id: r.document_id,
        doc_title: r.doc_title || "Untitled",
        doc_source: r.doc_source || "manual",
        rank: r.rank || 0,
      }));
    }
    return [];
  }

  return matched.map((s, i) => ({
    id: s.chunk.id,
    content: s.chunk.content,
    document_id: s.chunk.document_id,
    doc_title: s.chunk.documents?.title || "Untitled",
    doc_source: s.chunk.documents?.source_id || "manual",
    rank: (limit - i) / limit,
  }));
}

/* ── LLM call ─────────────────────────────────────────────────────────────── */

interface LLMMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

/**
 * Call the OpenCode Go API (OpenAI-compatible) for chat completion.
 */
async function callLLM(
  messages: LLMMessage[],
  temperature = 0.3,
): Promise<string | null> {
  try {
    const res = await fetch(`${OPENAI_BASE_URL}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: CHAT_MODEL,
        messages,
        temperature,
        max_tokens: MAX_TOKENS,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      console.error(`LLM API error ${res.status}: ${text}`);
      return null;
    }

    const data = await res.json();
    return data.choices?.[0]?.message?.content || null;
  } catch (err) {
    console.error("LLM call failed:", err);
    return null;
  }
}

/* ── Answer ───────────────────────────────────────────────────────────────── */

const SYSTEM_PROMPT = `You are ErgeneAI Brain, a helpful AI knowledge base assistant for ErgeneAI.

Your job:
- Answer questions based ONLY on the provided context chunks.
- If the context doesn't contain enough information, say "Bu bilgi knowledge base'de bulunamadı."
- Always cite sources using [1], [2] etc. referencing the source documents.
- Be concise, direct, and helpful.
- Answer in the same language as the question (Türkçe or English).
- Format answers in clear paragraphs. Use markdown for emphasis.

CRITICAL: Never make up facts. Only use information from the provided context.`;

/**
 * Generate an answer using RAG: search → context → LLM → answer.
 */
export async function ask(
  question: string,
): Promise<RagResult> {
  // 1. Search for relevant chunks
  const chunks = await searchChunks(question);

  if (chunks.length === 0) {
    return {
      answer:
        "Bu soruyla ilgili knowledge base'de henüz bir bilgi bulunamadı. Lütfen daha farklı bir şekilde sormayı deneyin veya ilgili dokümanı ekleyin.",
      citations: [],
      confidence: 0,
    };
  }

  // 2. Build context from chunks
  const context = chunks
    .map(
      (c, i) =>
        `[${i + 1}] Kaynak: "${c.doc_title}"\nİçerik: ${c.content}`,
    )
    .join("\n\n---\n\n");

  const sourcesInfo = chunks
    .map(
      (c, i) =>
        `[${i + 1}] ${c.doc_title}`,
    )
    .join("\n");

  // 3. Build messages
  const messages: LLMMessage[] = [
    { role: "system", content: SYSTEM_PROMPT },
    {
      role: "user",
      content: `Aşağıdaki bilgi tabanı belgelerine göre soruyu cevapla.\n\nSORU: ${question}\n\nKAYNAK BELGELER:\n${context}\n\nKULLANILABİLİR KAYNAKLAR:\n${sourcesInfo}\n\nCEVAP:`,
    },
  ];

  // 4. Call LLM
  const answerText = await callLLM(messages);

  if (!answerText) {
    return {
      answer: "Üzgünüm, şu anda yanıt üretilemiyor. Lütfen daha sonra tekrar deneyin.",
      citations: chunks.map((c) => ({
        title: c.doc_title,
        source: c.doc_source,
        docId: c.document_id,
      })),
      confidence: 0,
    };
  }

  // 5. Build citations
  const citedChunks = chunks.filter((_, i) => {
    // Check if this source index was referenced in the answer
    const idx = i + 1;
    return answerText.includes(`[${idx}]`) || answerText.includes(`[${idx}]`);
  });

  const citations = (citedChunks.length > 0 ? citedChunks : chunks.slice(0, 2)).map((c) => ({
    title: c.doc_title,
    source: c.doc_source,
    docId: c.document_id,
  }));

  // 6. Estimate confidence based on search rank
  const avgRank = chunks.reduce((sum, c) => sum + c.rank, 0) / chunks.length;
  const confidence = Math.min(0.98, Math.max(0.1, avgRank / 10));

  // 7. Log the question & answer
  await supabaseAdmin.from("questions").insert({
    question,
    answer: answerText,
    answer_sources: JSON.stringify(citations),
    confidence,
    status: "answered",
  });

  return {
    answer: answerText,
    citations,
    confidence,
  };
}
