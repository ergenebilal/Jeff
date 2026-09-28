# JCode Spark Model Flag Pitfall (2026-08-20)

## Symptom
```
jcode run "prompt"  # without -m flag
→ Error: OpenAI-compatible chat request failed
  endpoint: https://opencode.ai/zen/go/v1/chat/completions
  model: anthropic/claude-sonnet-4
  auth: OPENAI_COMPAT_API_KEY
  status: 401 Unauthorized
  response: {"type":"error","error":{"type":"ModelError","message":"Model anthropic/claude-sonnet-4 is not supported"}}
```

## Root Cause
`jcode` binary hardcodes `anthropic/claude-sonnet-4` as the default model when `run` is called without `-m`. It does NOT pick up `~/.jcode/config.toml:default_model` (`muse-spark-1.2-contributor`) for the `run` subcommand — config.toml is read but the hardcoded default wins for non-interactive `run`.

Even though `~/.jcode/config.toml` contains:
```
default_model = "muse-spark-1.2-contributor"
default_provider = "openai-compatible"
```
`jcode run "prompt"` still sends `anthropic/claude-sonnet-4` to the opencode-go endpoint, which rejects it (401).

## Fix
Always pass `-m` explicitly:

```bash
# ❌ Wrong — sends anthropic/claude-sonnet-4 → 401
jcode run "do something"

# ✅ Correct — sends muse-spark-1.2-contributor → 200
jcode run -m muse-spark-1.2-contributor "do something"

# ✅ Also correct for background
jcode run -m muse-spark-1.2-contributor "$(cat spec.md)"
```

Verification:
```bash
jcode run -m muse-spark-1.2-contributor "Say exactly: jcode-spark-ok"
# → jcode-spark-ok  [Tokens] upload: 14059 ...
```

## When This Bites
- `terminal(background=True)` with `jcode run "spec"` — the single most common delegation pattern.
- Any `jeff-coding-agent` workflow that omits `-m`.

## Workaround Alternatives Considered
- Patching `~/.jcode/config.toml` alone → insufficient.
- `jcode login --provider opencode-go` → still sends wrong model.
- `jcode -p openai-compatible -m ...` → `-p` flag rejected when combined with `-m` in some versions; use `-m` only.

## Prevention
The `coding-policy` skill routing pseudocode now mandates `-m muse-spark-1.2-contributor` in all `jcode run` examples. Any template that generates a `jcode run` command must include `-m`.
