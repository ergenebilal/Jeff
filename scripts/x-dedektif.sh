#!/bin/bash
# X Dedektif Ajanı — Grok 4.20 ile X araştırması
# harici LLM provider API üzerinden çalışır

# API Key
API_KEY=$(grep LLM_PROVIDER_API_KEY /home/hermes/.hermes/.env 2>/dev/null | head -1 | cut -d= -f2-)
if [ -z "$API_KEY" ]; then
    echo "[SILENT]"
    exit 0
fi

# Prompt
read -r -d '' PROMPT << 'PROMPTEOF'
Sen bir X/Twitter dedektifisin. Görevin:
1. X'te son 7 günde AI agent, solopreneur, no-code, automation konularındaki trendleri tara
2. Türkiye'deki AI girişimcilik ekosisteminde öne çıkan konuşmaları yakala
3. ErgeneAI'nin yararlanabileceği fırsatları tespit et (yeni araçlar, pazar boşlukları, iş modelleri)
4. Varsa rakip analizi yap (benzer hizmet verenler, fiyatlandırmaları)
5. Dikkat çekici bir şey varsa öne çıkar

CEVAP FORMATI (Türkçe):
🕵️ X Dedektif Raporu

📊 Bu Haftanın Trendleri:
- [madde]

🎯 Fırsatlar:
- [madde]

👀 Dikkat Çekenler:
- [madde]

🔮 Tahmin/Öneri:
- [kısa öneri]

EĞER hiçbir önemli veya yeni bir şey yoksa, sadece "[SILENT]" yaz.
PROMPTEOF

# Call Grok via harici LLM provider
RESPONSE=$(curl -s https://harici-provider.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -H "HTTP-Referer: https://ergeneai.xyz" \
  -d "$(cat << JSONEOF
{
  "model": "x-ai/grok-4.20",
  "messages": [
    {"role": "system", "content": "You are an X/Twitter detective. You read X platform trends and report findings."},
    {"role": "user", "content": $(echo "$PROMPT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")}
  ],
  "max_tokens": 800,
  "temperature": 0.5
}
JSONEOF
)")

# Parse response
CONTENT=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'choices' in data:
        print(data['choices'][0]['message']['content'])
    elif 'error' in data:
        print('[SILENT]')
    else:
        print('[SILENT]')
except:
    print('[SILENT]')
")

echo "$CONTENT"
