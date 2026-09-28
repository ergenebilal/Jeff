#!/bin/bash
# NVIDIA NIM (veya herhangi bir OpenAI-uyumlu API) model canlılık taraması
# /v1/models listesinde görünen her model çağrılabilir DEĞİLDİR (404/410/000).
# Bu script her modeli tek tek POST /chat/completions ile test eder,
# sadece HTTP 200'ler 'çalışıyor' sayılır.
#
# Kullanım: bash nvidia-probe.sh [model1 model2 ...]
# Model verilmezse varsayılan liste test edilir. Key: ~/.hermes/.env NVIDIA_API_KEY
set -u

KEY=$(grep NVIDIA_API_KEY ~/.hermes/.env | cut -d= -f2)
BASE="${NVIDIA_BASE_URL:-https://integrate.api.nvidia.com/v1}"
OUT="${NVIDIA_PROBE_LOG:-/home/hermes/logs/nvidia-probe-$(date +%Y%m%d-%H%M).log}"

if [ $# -gt 0 ]; then
  MODELS=("$@")
else
  MODELS=(
    "deepseek-ai/deepseek-v4-flash-0731"
    "deepseek-ai/deepseek-v4-pro-0813"
    "openai/gpt-oss-20b"
    "nvidia/nemotron-3-ultra-550b-a55b"
    "minimaxai/minimax-m3"
    "meta/llama-3.2-90b-vision-instruct"
    "nvidia/llama-3.1-nemotron-ultra-253b-v1"
  )
fi
TIMEOUT="${NVIDIA_PROBE_TIMEOUT:-45}"

echo "=== NVIDIA PROBE $(date '+%H:%M:%S') — ${#MODELS[@]} model ===" | tee "$OUT"
for m in "${MODELS[@]}"; do
  T1=$(date +%s.%N)
  HTTP=$(curl -s -o /tmp/nvresp.json -w "%{http_code}" -m "$TIMEOUT" "$BASE/chat/completions" \
    -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
    -d "{\"model\":\"$m\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly: OK\"}],\"max_tokens\":5}" 2>/dev/null)
  T2=$(date +%s.%N)
  ELAPSED=$(echo "$T2 $T1" | awk '{printf "%.1f", $1-$2}')
  if [ "$HTTP" = "200" ]; then
    REPLY=$(python3 -c "import json;print(json.load(open('/tmp/nvresp.json')).get('choices',[{}])[0].get('message',{}).get('content','')[:40])" 2>/dev/null)
    echo "OK   $m — HTTP 200 (${ELAPSED}s) → '$REPLY'" | tee -a "$OUT"
  else
    ERR=$(head -c 120 /tmp/nvresp.json 2>/dev/null | tr -d '\n')
    echo "FAIL $m — HTTP $HTTP (${ELAPSED}s) → $ERR" | tee -a "$OUT"
  fi
done
echo "=== BITTI $(( $(date +%s) - ${T1%%.*} ))s — log: $OUT ===" | tee -a "$OUT"
exit 0