#!/bin/bash
# Model switcher for Jeff — OpenCode Go
# Usage: switch-model.sh <model>
# Models: flash, pro, glm, qwen, kimi, mimo, minimax

case "$1" in
  flash)
    hermes config set model.default deepseek-v4-flash
    echo "🟢 V4 Flash — hafif işler"
    ;;
  pro)
    hermes config set model.default deepseek-v4-pro
    echo "🟡 V4 Pro — orta işler"
    ;;
  glm)
    hermes config set model.default glm-5.2
    echo "🔴 GLM-5.2 — ağır işler"
    ;;
  qwen)
    hermes config set model.default qwen3.7-max
    echo "🔴 Qwen3.7 Max — ağır işler"
    ;;
  kimi)
    hermes config set model.default kimi-k2.7-code
    echo "🟣 Kimi K2.7 Code — kod ağırlıklı"
    ;;
  mimo)
    hermes config set model.default mimo-v2.5
    echo "🟢 MiMo V2.5 — ultra hafif"
    ;;
  mini)
    hermes config set model.default minimax-m3
    echo "🟡 MiniMax M3 — orta"
    ;;
  status)
    echo "Mevcut model: $(hermes config get model.default 2>/dev/null || grep 'default:' ~/.hermes/config.yaml | head -1)"
    echo "Provider: opencode-go"
    ;;
  *)
    echo "Kullanım: switch-model.sh {flash|pro|glm|qwen|kimi|mimo|mini|status}"
    echo ""
    echo "  flash   → deepseek-v4-flash  🟢 (default, hafif)"
    echo "  pro     → deepseek-v4-pro    🟡"
    echo "  glm     → glm-5.2            🔴 (en zeki)"
    echo "  qwen    → qwen3.7-max        🔴"
    echo "  kimi    → kimi-k2.7-code     🟣 (kod)"
    echo "  mimo    → mimo-v2.5          🟢 (ultra hafif)"
    echo "  mini    → minimax-m3         🟡"
    exit 1
    ;;
esac
