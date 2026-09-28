#!/bin/bash
# OpenCode native ile Tool Hunter - maliyet: $0
export PATH="/home/hermes/.hermes/node/bin:$PATH"
cd /home/hermes
opencode run --agent operator . "
Gozden gecirilecek kaynaklar:
1. X/Twitter: AI ve startup dunyasinda yeni tool'lar
2. Reddit: r/AIAgents, r/SaaS, r/indiehackers
3. GitHub: trend repos

Gorevlerin:
1. X/Twitter'da AI agent aracı ve yeni tool lansmanlarını tara
2. Reddit'te r/AIagents, r/SaaS, r/indiehackers'daki populer posting'leri oku
3. GitHub trending'de AI agent/tool kategorisini kontrol et

Her kaynaktan en fazla 3 yeni/dikkat cekici sey bul.
Ciktiyi /home/hermes/.hermes/raporlar/tool-hunter-sonuc.md'ye yaz.
"
