#!/bin/bash
# /durum komutu — KÖKLEŞME Motoru üzerinden anlık durum raporu
# Kullanım: bash ~/.hermes/scripts/durum.sh

SCRIPT_DIR="$HOME/.hermes/scripts"
MOTOR="$SCRIPT_DIR/koklesme_motoru.py"

# Renkler
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     KÖKLEŞME MOTORU — Durum Raporu     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

if [ ! -f "$MOTOR" ]; then
    echo "❌ HATA: KÖKLEŞME Motoru bulunamadı: $MOTOR"
    exit 1
fi

python3 "$MOTOR" --durum

echo ""
echo -e "${BLUE}────────────────────────────────────────────${NC}"
echo -e "${YELLOW}💡 İpuçları:${NC}"
echo -e "  ${YELLOW}→${NC} Detaylı özet:  python3 $MOTOR --hersey"
echo -e "  ${YELLOW}→${NC} Sabah brifingi: python3 $MOTOR --sabah"
echo -e "  ${YELLOW}→${NC} Bugünün odağı: python3 $MOTOR --odak"
echo -e "  ${YELLOW}→${NC} Karar destek:   python3 $MOTOR --karar \"sorunuz\""
echo ""
