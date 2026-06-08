#!/bin/bash
# PAZARLAMA MOTORU - n8n + Hermes cron ile tam otonom
# Bu script API key'ler girildikten sonra tüm platformları başlatır

echo "========== PAZARLAMA MOTORU =========="
echo "Kurulum başlıyor..."

# 1. Gerekli Python paketleri
pip3 install fpdf2 2>/dev/null

# 2. Git reposu hazırla
cd /home/hermes/dijital-urunler
git init 2>/dev/null
git add -A
git commit -m "v1.0 - Digital product packages" 2>/dev/null

echo ""
echo "==========================================="
echo "PAZARLAMA MOTORU HAZIR"
echo ""
echo "EKSIK API KEY'LER (gelince aktiflesir):"
echo "  - Twitter API key     -> /home/hermes/.hermes/secrets/twitter.json"
echo "  - YouTube API key     -> /home/hermes/.hermes/secrets/youtube.json"
echo "  - Stripe/Gumroad      -> web'den Stripe bagla"
echo ""
echo "Hazir bekliyor. API key'ler girilince:"
echo "  1. X/Twitter thread   -> n8n cron (haftada 3)"
echo "  2. Reddit post        -> Agent Reach (haftada 2)"
echo "  3. YouTube Shorts     -> n8n cron (haftada 1)"
echo "  4. Gumroad Discover   -> SEO optimizasyonu"
echo "==========================================="
