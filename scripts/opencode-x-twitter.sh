#!/bin/bash
# OpenCode native ile X/Twitter paylasimi - maliyet: $0
export PATH="/home/hermes/.hermes/node/bin:$PATH"
cd /home/hermes
opencode run --agent operator . "
Gorev: ErgeneAI adina X/Twitter'da haftalik icerik paylasimi.

KONU: Gumroad urun tanitimi sirasi.
Urunler (sirayla):
1. n8n Ultimate Workflow Pack (\$19.99 - 32 workflow)
2. Zero to AI Agent (\$14.99 - sifirdan AI ordusu)
3. Prompt Engineering for Agents (\$9.99 - 200+ prompt)
4. AI Agency Starter Kit (\$24.99 - ajans baslangic paketi)
5. n8n Brand & Lead Monitoring Pack (\$19.99 - otomatik lead avi)

Format:
- 2-3 tweet'lik mini thread
- Ilk tweet: sorun/sorun tanimi
- Ikinci tweet: cozum (urun)
- Son tweet: link + CTA

Marka kurali:
- 'ErgeneAI'den Bilal' imzasi
- 'AI Agent' YASAK - 'AI Personel' / 'Dijital Calisan' kullan
- Kisa, oz, deger odakli

Icercigi /home/hermes/x-content/output-\$(date +%Y%m%d).md dosyasina kaydet.
XActions MCP calisiyorsa direkt paylas, calismiyorsa icerigi kaydet ve manuel paylasim icin bildir.
"
