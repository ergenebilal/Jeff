#!/usr/bin/env bash
# CyberGene Aider-Antigravity Kodlama Scripti
# Kullanım: aider-code "Görev açıklaması" [dosya1 dosya2 ...]

if [ -z "${1:-}" ]; then
  echo "Kullanım: aider-code \"Görev açıklaması\" [dosya1 dosya2 ...]"
  exit 1
fi

MSG="$1"
shift

# Antigravity Proxy Ortam Değişkenleri
export OPENAI_API_BASE="http://127.0.0.1:8999/v1"
export OPENAI_API_KEY="antigravity"

# Aider'ı Claude 3.5 Sonnet ile tetikle
aider --model openai/claude-3-5-sonnet-latest \
      --no-show-model-warnings \
      --message "$MSG" \
      "$@"
