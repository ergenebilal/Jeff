#!/bin/bash
# Cron Gece Keşif Wrapper — VAROLUŞ Motoru
# Her gece ~03:00'te çalışır.
# Kullanım: bash ~/.hermes/scripts/cron_gece_kesfi.sh
# Cron: 0 3 * * * /home/hermes/.hermes/scripts/cron_gece_kesfi.sh

SCRIPT_DIR="$HOME/.hermes/scripts"
LOG_DIR="$HOME/.hermes/kesif_raporlari"
MOTOR="$SCRIPT_DIR/varolus_motoru.py"
LOCKFILE="/tmp/varolus_gece_kesfi.lock"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Log dizinini oluştur
mkdir -p "$LOG_DIR"

# Lock kontrolü — zaten çalışıyorsa çık
if [ -f "$LOCKFILE" ]; then
    echo "[$TIMESTAMP] ⚠️  Gece keşfi zaten çalışıyor. Çıkılıyor."
    exit 1
fi

# Lock oluştur
touch "$LOCKFILE"

# Trap ile lock temizleme
cleanup() {
    rm -f "$LOCKFILE"
}
trap cleanup EXIT

echo "[$TIMESTAMP] 🌙 Gece keşfi başlatılıyor..."
echo "[$TIMESTAMP] Motor: $MOTOR"

# VAROLUŞ Motoru'nu çalıştır
python3 "$MOTOR" --kesif

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$TIMESTAMP] ✅ Gece keşfi başarıyla tamamlandı."
    
    # En son raporu göster
    LATEST_REPORT=$(ls -t "$LOG_DIR"/kesif_raporu_*.md 2>/dev/null | head -1)
    if [ -n "$LATEST_REPORT" ]; then
        echo "[$TIMESTAMP] 📄 Rapor: $LATEST_REPORT"
    fi
else
    echo "[$TIMESTAMP] ❌ Gece keşfi başarısız oldu (exit code: $EXIT_CODE)."
fi

echo "[$TIMESTAMP] 🏁 Tamamlandı."
exit $EXIT_CODE
