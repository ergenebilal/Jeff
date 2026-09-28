"use client";

import { useEffect, useRef, useState } from "react";
import { Sparkles, ArrowUp, FileText, RotateCcw, AlertCircle } from "lucide-react";
import { useLang } from "@/components/i18n/language-provider";
import { cn } from "@/lib/utils";

interface Citation {
  title: string;
  source: string;
  docId: string;
}

interface RagResult {
  answer: string;
  citations: Citation[];
  confidence: number;
}

const SUGGESTIONS: Record<string, string[]> = {
  tr: [
    "ErgeneAI hangi hizmetleri sunuyor?",
    "Kurulum ne kadar sürüyor?",
    "Müşteri başarı hikayeleriniz neler?",
    "Brain nasıl çalışıyor?",
  ],
  en: [
    "What services does ErgeneAI offer?",
    "How long does setup take?",
    "What are your customer success stories?",
    "How does Brain work?",
  ],
};

function SourceIconFallback({ source, size = 16 }: { source: string; size?: number }) {
  const colors: Record<string, string> = {
    manual: "bg-blue-500",
    notion: "bg-black dark:bg-white",
    drive: "bg-green-500",
    slack: "bg-purple-500",
  };
  return (
    <span
      className={`grid shrink-0 place-items-center rounded-[4px] text-[9px] font-bold text-white ${colors[source] || "bg-primary"}`}
      style={{ width: size, height: size }}
    >
      {(source[0] || "K").toUpperCase()}
    </span>
  );
}

export function AskBar({ variant = "full" }: { variant?: "full" | "hero" }) {
  const { lang } = useLang();
  const [input, setInput] = useState("");
  const [answer, setAnswer] = useState<RagResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [shown, setShown] = useState(0);
  const [thinking, setThinking] = useState(false);
  const [streamed, setStreamed] = useState("");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const suggestions = SUGGESTIONS[lang] || SUGGESTIONS.en;

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
    if (abortRef.current) abortRef.current.abort();
  }, []);

  async function askAPI(question: string) {
    // Cancel any previous request
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    setThinking(true);
    setError(null);
    setAnswer(null);
    setShown(0);
    setStreamed("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "Bir hata oluştu." }));
        throw new Error(err.error || `HTTP ${res.status}`);
      }

      const data: RagResult = await res.json();

      if (!data.answer || data.answer.length === 0) {
        throw new Error("Boş yanıt alındı.");
      }

      setAnswer(data);

      // Stream the answer word-by-word
      setThinking(false);
      const full = data.answer;
      let i = 0;
      const tick = () => {
        i += Math.max(2, Math.round(full.length / 80));
        const nextI = Math.min(i, full.length);
        setShown(nextI);
        setStreamed(full.slice(0, nextI));
        if (nextI < full.length) {
          timer.current = setTimeout(tick, 14);
        }
      };
      tick();
    } catch (err: any) {
      if (err.name === "AbortError") return;
      setThinking(false);
      setError(err.message || "Bir hata oluştu. Lütfen daha sonra tekrar deneyin.");
    }
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    askAPI(input.trim());
  }

  function pickSuggestion(q: string) {
    setInput("");
    askAPI(q);
  }

  const done = !thinking && shown > 0 && streamed.length > 0 && shown >= (answer?.answer?.length || 0);

  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-card shadow-soft",
        variant === "hero" && "shadow-pop",
      )}
    >
      {/* Input */}
      <form onSubmit={submit} className="flex items-center gap-2.5 p-3 sm:p-3.5">
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
          <Sparkles className="h-[18px] w-[18px]" />
        </span>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={lang === "tr" ? "ErgeneAI'ye bir şey sor…" : "Ask ErgeneAI anything…"}
          className="min-w-0 flex-1 bg-transparent text-[15px] text-foreground placeholder:text-muted-foreground/70 focus:outline-none"
        />
        <button
          type="submit"
          aria-label={lang === "tr" ? "Sor" : "Ask"}
          className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-40"
          disabled={!input.trim() || thinking}
        >
          <ArrowUp className="h-[18px] w-[18px]" />
        </button>
      </form>

      {/* Suggestion chips */}
      <div className="flex flex-wrap gap-1.5 border-t border-border px-3.5 py-2.5">
        {suggestions.map((q) => (
          <button
            key={q}
            onClick={() => pickSuggestion(q)}
            disabled={thinking}
            className="rounded-full border border-border bg-card px-2.5 py-1 text-[12px] text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Error state */}
      {error && (
        <div className="border-t border-border p-3.5 sm:p-4">
          <div className="flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-3">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
            <div>
              <p className="text-sm font-medium text-destructive">
                {lang === "tr" ? "Hata" : "Error"}
              </p>
              <p className="mt-0.5 text-[13px] text-foreground/80">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Answer */}
      {(thinking || streamed) && !error && (
        <div className="border-t border-border p-3.5 sm:p-4">
          <div className="mb-2 flex items-center gap-2">
            <span className="label-mono text-muted-foreground">{lang === "tr" ? "Brain yanıtı" : "Brain answer"}</span>
            {done && answer && (
              <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-1.5 py-0.5 text-[10px] font-semibold text-success">
                {Math.round(answer.confidence * 100)}% {lang === "tr" ? "güven" : "confidence"}
              </span>
            )}
            {done && (
              <button
                onClick={() => {
                  const q = input || answer?.citations?.[0]?.title || "";
                  if (q) askAPI(q);
                }}
                className="ml-auto inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <RotateCcw className="h-3 w-3" />
                {lang === "tr" ? "Yeniden" : "Regenerate"}
              </button>
            )}
          </div>

          {thinking && !streamed ? (
            <div className="flex items-center gap-1.5 py-1">
              {[0, 1, 2].map((i) => (
                <span key={i} className="think-dot h-2 w-2 rounded-full bg-primary" style={{ animationDelay: `${i * 0.18}s` }} />
              ))}
              <span className="ml-1 text-[13px] text-muted-foreground">{lang === "tr" ? "Kaynaklar taranıyor…" : "Searching your sources…"}</span>
            </div>
          ) : (
            <p className="text-[14.5px] leading-relaxed text-foreground">
              {streamed}
              {!done && <span className="caret ml-0.5 inline-block h-4 w-[2px] -translate-y-0.5 bg-primary align-middle" />}
            </p>
          )}

          {/* Citations */}
          {done && answer && answer.citations.length > 0 && (
            <div className="mt-3.5 animate-fade-in">
              <p className="label-mono mb-1.5 text-muted-foreground">{lang === "tr" ? "Kaynaklar" : "Sources"}</p>
              <div className="flex flex-wrap gap-2">
                {answer.citations.map((c, i) => (
                  <span
                    key={`${c.docId}-${i}`}
                    className="inline-flex items-center gap-2 rounded-lg border border-border bg-muted/40 py-1 pl-1.5 pr-2.5 text-[12.5px] transition-colors hover:bg-muted"
                  >
                    <span className="grid h-5 w-5 shrink-0 place-items-center rounded-md bg-card text-[10px] font-bold text-muted-foreground ring-1 ring-border">
                      {i + 1}
                    </span>
                    <SourceIconFallback source={c.source} size={16} />
                    <span className="font-medium">{c.title}</span>
                    <FileText className="h-3 w-3 text-muted-foreground" />
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
