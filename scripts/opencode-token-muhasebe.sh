#!/bin/bash
# OpenCode native ile Token Muhasebesi - maliyet: $0
export PATH="/home/hermes/.hermes/node/bin:$PATH"
cd /home/hermes
opencode run --agent operator . "
Token muhasebesi raporu hazirla.

Kontrol et:
1. n8n servis calismalari - bugun AI cagiran workflow var mi?
2. Hermes session tahmini - bugunku konusma yogunlugu
3. OpenCode aktivitesi (DeepSeek butcesini etkilemez)

Raporu /home/hermes/token-muhasebe/output-\$(date +%Y%m%d).md dosyasina yaz:
- Bugun: ~tahmini token / ~tahmini $ maliyet
- Bu hafta: ~tahmini token / ~tahmini $ maliyet
- Saglik durumu (Yesil/Sari/Kirmizi)
"
