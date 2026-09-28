# Spark 1.2 Contributor Migration — 20.08.2026

## Context
Hermes/JCode/Claude Code proxy hepsi opencode-go üzerinden `muse-spark-1.2-contributor`'a geçirildi.
- Model: Meta 06.08.2026, Muse Code co-train, 1M ctx multimodal, agentic+reasoning.
- Fiyat: $0.10/$0.20/$0.002 Contributor tier, limit $12/5s $30/hft $60/ay, opt-in training onaylı (X tweet 2090158371097698394).
- Proxy: `claude_opencode_proxy.py` MODEL_MAP 12 entry Spark'a patch (+ fallback), `~/.config/opencode/opencode.jsonc` operator+jeff-subagent Spark.

## Pitfall — JCode default model hardcode
- `jcode run "prompt"` tek başına `anthropic/claude-sonnet-4` gönderir → Zen `401 Model not supported`.
- `~/.jcode/config.toml:default_model` yetmez.
- Fix: her zaman `-m muse-spark-1.2-contributor` ekle: `jcode run -m muse-spark-1.2-contributor "prompt"`

## Verification
- `curl zen/go/v1/chat/completions -d model=spark` → "Hello, it's so nice to meet you!"
- `curl localhost:8098/v1/messages -d model=claude-sonnet-4` → "Hello, I'm Muse Spark" (proxy mapping)
- Workflow #1: Claude 13dk 76 tur loop (0 artifact) → JCode Spark 5dk'da DB INSERT (7 node workflow). Aynı model, harness farkı.

## Timeout Tuning for Spark (agentic reasoning uzun)
- `~/.claude/settings.json: API_TIMEOUT_MS=900000 (15dk)`, `~/.hermes/config.yaml: gateway_timeout=3600s (60dk)`, `max_turns=150`, `stream_idle=180s`
- Kural: Spark kesilmemeli — background+notify_on_complete kullan, 12dk+ reasoning normal.

## Delegation Impact
- Fiyat/model farkı kalmadı (her iki worker Spark), seçim zorluğa göre kas ile yapılır.
- Ağır n8n multi-node/retry/dedup → Claude Code (co-train avantajı SWE 83% / Terminal-Bench 82.9%).
- Hafif/orta tek dosya/script → JCode (swarm 32, 39MB, 12sn).

## References
- `/tmp/jcode-w1-spec.md` (54 satır), `/tmp/jcode-w1.log`, `claude_opencode_proxy.py.bak-mimo-20260820`
