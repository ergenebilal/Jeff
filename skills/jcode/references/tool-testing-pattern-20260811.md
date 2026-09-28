# Tool Testing Pattern — 11.08.2026

## Test Setup
- jcode + Claude Code parallel execution
- Both use same OpenCode Go API key via proxy

## Test Results

| Task | Tool | Result | Notes |
|------|------|--------|-------|
| requirements.txt | jcode | ✅ | 136 files, 856 imports, 8 packages kept |
| self_healing.py | Claude Code | ✅ | 272→573 lines, restart added |
| approval_gateway.py | Claude Code `--print` | ❌ | Sandbox can't write files |
| approval_gateway.py | Hermes write_file | ✅ | After Claude generated code |

## Key Findings

### 1. jcode API Key Must Match Proxy
```bash
# Get key from proxy
grep "OPENCODE_KEY = " /opt/hermes/jeff_v2/claude_opencode_proxy.py

# Set in jcode config
cat > ~/.config/jcode/openai-compatible.env << EOF
JCODE_OPENAI_COMPAT_API_BASE=https://opencode.ai/zen/go/v1
OPENAI_COMPAT_API_KEY=$KEY
EOF
```

### 2. Claude Code `--print` Sandbox Limitation
- `--print` mode cannot write files to disk
- Workaround: Claude generates code, Hermes writes via write_file
- Interactive mode (`claude` without `--print`) may have write access

### 3. Background Execution Pattern
```python
# ✅ Correct — background with notify
terminal("command", background=True, notify_on_complete=True)

# ❌ Wrong — foreground with timeout risk
terminal("command", timeout=60)
```

### 4. Parallel Tool Testing
- Run both tools in background simultaneously
- Poll for completion
- Verify outputs independently
- Document which tool succeeded/failed for each task

## User Corrections
- "zaman aşımı sorunu kabul edilemez!" — always use background for long tasks
- "hayır, claude code a yaptıracaksın" — purpose is testing tools, not doing work myself
- "bu görevlerin amacı onu test etmek!" — delegate to tools, don't substitute
