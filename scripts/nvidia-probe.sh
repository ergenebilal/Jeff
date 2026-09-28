#!/bin/bash
# NVIDIA NIM model probe — hangi modeller gerçekten yanıt veriyor?
KEY=$(grep NVIDIA_API_KEY ~/.hermes/.env | cut -d= -f2)
BASE="https://integrate.api.nvidia.com/v1"
OUT="/home/hermes/logs/nvidia-probe-$(date +%Y%m%d-%H%M).log"
MODELS=(
  "deepseek-ai/deepseek-v4-flash-0731"
  "deepseek-ai/deepseek-v4-pro-0813"
  "meta/llama-3.2-90b-vision-instruct"
  "nvidia/llama-3.1-nemotron-ultra-253b-v1"
  "openai/gpt-oss-20b"
  "mistralai/mistral-large-2"
  "meta/llama-3.1-8b-instruct"
)
T0=$(date +%s)
echo "=== NVIDIA PROBE BAŞLANGIÇ $(date '+%H:%M:%S') ===" | tee "$OUT"
for m in "${MODELS[@]}"; do
  T1=$(date +%s.%N)
  HTTP=$(curl -s -o /tmp/nvresp.json -w "%{http_code}" -m 45 "$BASE/chat/completions" \
    -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
    -d "{\"model\":\"$m\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly: OK\"}],\"max_tokens\":5}" 2>/dev/null)
  T2=$(date +%s.%N)
  ELAPSED=$(echo "$T2 $T1" | awk '{printf "%.1f", $1-$2}')
  if [ "$HTTP" = "200" ]; then
    REPLY=$(python3 -c "import json;print(json.load(open('/tmp/nvresp.json')).get('choices',[{}])[0].get('message',{}).get('content','')[:40])" 2>/dev/null)
    echo "✅ $m — HTTP 200 (${ELAPSED}s) → '$REPLY'" | tee -a "$OUT"
  else
    ERR=$(head -c 120 /tmp/nvresp.json 2>/dev/null)
    echo "❌ $m — HTTP $HTTP (${ELAPSED}s) → $ERR" | tee -a "$OUT"
  fi
done
TEND=$(date +%s)
echo "=== PROBE BİTTİ — toplam $((TEND-T0))s ===" | tee -a "$OUT"
echo "LOGFILE=$OUT"