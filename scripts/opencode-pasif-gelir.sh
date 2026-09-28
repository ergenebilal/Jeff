#!/bin/bash
# OpenCode native ile Pasif Gelir Firsat Raporu - maliyet: $0
export PATH="/home/hermes/.hermes/node/bin:$PATH"
cd /home/hermes
opencode run --agent operator . "
Haftalik pasif gelir firsat raporu hazirla.

Kaynaklari tara:
1. Gumroad dashboard - satis trendleri
2. Dijital urun pazari - rakip analizi
3. Yeni pasif gelir firsatlari (AI trendleri)

Raporu /home/hermes/pasif-gelir/output-\$(date +%Y%m%d).md dosyasina yaz:
- Mevcut urunlerin durumu
- Yeni firsatlar
- Aksiyon onerileri (onecelik sirali)
"
