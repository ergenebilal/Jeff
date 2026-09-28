#!/bin/bash
# LLM Health Check - günlük DeepSeek sağlık kontrolü
# no_agent=true ile çalışır, stdout'a yazdığı her şey direkt mesaj olarak gider

set -e

DEEPSEEK_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2 | tr -d '"' | tr -d "'" | tr -d ' ')

if [ -z "$DEEPSEEK_KEY" ]; then
    printf "⚠️ DEEPSEEK_API_KEY bulunamadi.\n.env dosyasini kontrol et."
    exit 1
fi

RESPONSE=$(curl -s -w "\n%{http_code}" https://api.deepseek.com/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $DEEPSEEK_KEY" \
    -d '{
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "ok"}],
        "max_tokens": 2
    }' 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    BALANCE=$(curl -s https://api.deepseek.com/user/balance \
        -H "Authorization: Bearer $DEEPSEEK_KEY" 2>/dev/null | \
        python3 -c "import sys,json; d=json.load(sys.stdin); bi=d.get('balance_infos',[{}])[0]; print(f\"\${bi.get('total_balance','?')}\")" 2>/dev/null || echo "?")
    
    echo "✅ DeepSeek saglikli | Bakiye: $BALANCE | $(date '+%d.%m.%Y %H:%M')"
    exit 0
else
    echo "🔴 DeepSeek HATA (HTTP $HTTP_CODE)"
    echo "$BODY" | head -5
    exit 1
fi
