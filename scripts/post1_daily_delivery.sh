#!/usr/bin/env bash
# Daily delivery script — Post 1 Carousel
set -e
PIPELINE="/opt/hermes/instagram-pipeline-multi"
OUT="$PIPELINE/output"

echo "=== Post 1 — Günlük Teslimat ==="
echo ""

# Render
cd "$PIPELINE"
python3 render_carousel_v3.py 2>&1 | tail -5

echo ""
echo "=== Dosyalar ==="
for f in post1_slide{1,2,3,4,5}_v3.png; do
    SIZE=$(stat --format=%s "$OUT/$f" 2>/dev/null || echo "0")
    echo "file:$OUT/$f (${SIZE} bytes)"
done

echo ""
echo "=== Teslimat (Telegram) ==="
cd "$PIPELINE"
python3 deliver_cron.py 2>&1
echo ""
echo "=== Teslimat Tamamlandı ==="
