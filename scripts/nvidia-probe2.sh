#!/bin/bash
# NVIDIA NIM probe round 2 — güçlü/canlı model adayları (30s timeout)
KEY=$(grep NVIDIA_API_KEY ~/.hermes/.env | cut -d= -f2)
BASE="https://integrate.api.nvidia.com/v1"
OUT="/home/hermes/logs/nvidia-probe2-$(date +%Y%m%d-%H%M).log"
MODELS=(
  "mistralai/mistral-large"
  "mistralai/mistral-large-2-instruct"
  "nvidia/nemotron-3-ultra-550b-a55b"
  "nvidia/llama-3.1-nemotron-70b-instruct"
  "moonshotai/kimi-k2.6"
  "minimaxai/minimax-m3"
)
T0=$(date +%s)
echo "=== PROBE2 BAŞLANGIÇ $(date '+%H:%M:%S') ===" | tee "$OUT"
for m in "${MODELS[@]}"; do
  T1=$(date +%s.%N)
  HTTP=$(curl -s -o /tmp/nvresp2.json -w "%{http_code}" -m 30 "$BASE/chat/completions" \
    -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
    -d "{\"model\":\"$m\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly: OK\"}],\"max_tokens\":5}" 2>/dev/null)
  T2=$(date +%s.%N)
  EL=$(echo "$T2 $T1" | awk '{printf "%.1f", $1-$2}')
  if [ "$HTTP" = "200" ]; then
    R=$(python3 -c "import json;print(json.load(open('/tmp/nvresp2.json')).get('choices',[{}])[0].get('message',{}).get('content','')[:40])" 2>/dev/null)
    echo "✅ $m — HTTP 200 (${EL}s) → '$R'" | tee -a "$OUT"
  else
    E=$(head -c 80 /tmp/nvresp2.json 2>/dev/null)
    echo "❌ $m — HTTP $HTTP (${EL}s) → $E" | tee -a "$OUT"
  fi
done
echo "=== PROBE2 BİTTİ — $(( $(date +%s) - T0 ))s ===" | tee -a "$OUT"
echo "LOGFILE=$OUT"