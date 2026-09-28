#!/bin/bash
# Cron Health Check — SÜREKLİLİK Motoru
# Script/skill/cron bütünlük kontrolü.
# Kullanım: bash ~/.hermes/scripts/cron_health_check.sh
# Cron: */30 * * * * /home/hermes/.hermes/scripts/cron_health_check.sh

SCRIPT_DIR="$HOME/.hermes/scripts"
CHECKPOINT_DIR="$HOME/.hermes/checkpoint"
MEMORY_DIR="$HOME/.hermes/memories"
SKILL_DIR="$HOME/.hermes/skills/hermes-self"
LOG_DIR="$HOME/.hermes/logs"
LOCKFILE="/tmp/hermes_health_check.lock"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Log dizinini oluştur
mkdir -p "$LOG_DIR"

# Lock kontrolü
if [ -f "$LOCKFILE" ]; then
    LOCK_AGE=$(($(date +%s) - $(stat -c %Y "$LOCKFILE" 2>/dev/null || echo 0)))
    if [ "$LOCK_AGE" -lt 300 ]; then  # 5 dakikadan gençse hala çalışıyor
        echo "[$TIMESTAMP] ⚠️  Health check zaten çalışıyor (${LOCK_AGE}s). Çıkılıyor."
        exit 1
    else
        echo "[$TIMESTAMP] ⚠️  Eski lock bulundu (${LOCK_AGE}s), temizleniyor..."
        rm -f "$LOCKFILE"
    fi
fi

# Lock oluştur
touch "$LOCKFILE"

# Trap ile lock temizleme
cleanup() {
    rm -f "$LOCKFILE"
}
trap cleanup EXIT

echo "[$TIMESTAMP] 🏥 Health check başlatılıyor..."
echo ""

# ── 1. Python Script Bütünlük Kontrolü ──
echo "[$TIMESTAMP] 📜 Python script'leri kontrol ediliyor..."
SYNTAX_ERRORS=0
for script in "$SCRIPT_DIR"/*.py; do
    [ -f "$script" ] || continue
    if python3 -c "
import ast
try:
    with open('$script') as f:
        ast.parse(f.read())
    print('OK')
except SyntaxError as e:
    print(f'FAIL: {e}')
    exit(1)
" 2>/dev/null; then
        :  # OK
    else
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
        echo "[$TIMESTAMP]   ❌ $(basename "$script"): SYNTAX HATASI"
    fi
done

# ── 2. Skill Bütünlük Kontrolü ──
echo "[$TIMESTAMP] 🎯 Skill'ler kontrol ediliyor..."
SKILL_ERRORS=0
for skill_dir in "$SKILL_DIR"/*/; do
    [ -d "$skill_dir" ] || continue
    skill_name=$(basename "$skill_dir")
    skill_file="$skill_dir/SKILL.md"
    if [ ! -f "$skill_file" ]; then
        SKILL_ERRORS=$((SKILL_ERRORS + 1))
        echo "[$TIMESTAMP]   ❌ $skill_name: SKILL.md mevcut değil"
    elif ! grep -q "^name:" "$skill_file" 2>/dev/null; then
        SKILL_ERRORS=$((SKILL_ERRORS + 1))
        echo "[$TIMESTAMP]   ⚠️  $skill_name: SKILL.md'de 'name:' alanı eksik"
    fi
done

# ── 3. Checkpoint Bütünlük Kontrolü ──
echo "[$TIMESTAMP] 💾 Checkpoint kontrol ediliyor..."
CHECKPOINT_OK=0
if [ -f "$CHECKPOINT_DIR/checkpoint.json" ]; then
    if python3 -c "
import json
with open('$CHECKPOINT_DIR/checkpoint.json') as f:
    data = json.load(f)
required = ['aktif_faz', 'son_guncelleme', 'versiyon', 'motor', 'faz']
actual_required = ['aktif_faz', 'son_guncelleme', 'versiyon', 'motor', 'faz']
for field in actual_required:
    if field not in data:
        raise ValueError(f'Eksik alan: {field}')
print('OK')
" 2>/dev/null; then
        CHECKPOINT_OK=1
        echo "[$TIMESTAMP]   ✅ Checkpoint geçerli"
    else
        echo "[$TIMESTAMP]   ⚠️  Checkpoint bozuk, yedek kontrol ediliyor..."
        BACKUP=$(ls -t "$CHECKPOINT_DIR"/checkpoint_backup_*.json 2>/dev/null | head -1)
        if [ -n "$BACKUP" ]; then
            echo "[$TIMESTAMP]   ✅ Yedek mevcut: $(basename "$BACKUP")"
        else
            echo "[$TIMESTAMP]   ❌ Yedek bulunamadı!"
        fi
    fi
else
    echo "[$TIMESTAMP]   ❌ Checkpoint dosyası mevcut değil"
fi

# ── 4. Bellek Dosyası Kontrolü ──
echo "[$TIMESTAMP] 🧠 Bellek dosyaları kontrol ediliyor..."
MEMORY_ERRORS=0
for mem_file in "$MEMORY_DIR/MEMORY.md" "$MEMORY_DIR/USER.md"; do
    if [ ! -f "$mem_file" ]; then
        MEMORY_ERRORS=$((MEMORY_ERRORS + 1))
        echo "[$TIMESTAMP]   ❌ $(basename "$mem_file"): mevcut değil"
    elif [ ! -s "$mem_file" ]; then
        MEMORY_ERRORS=$((MEMORY_ERRORS + 1))
        echo "[$TIMESTAMP]   ⚠️  $(basename "$mem_file"): boş dosya"
    fi
done

# ── 5. Kritik Dizin Kontrolü ──
echo "[$TIMESTAMP] 📁 Dizinler kontrol ediliyor..."
DIR_ERRORS=0
for dir_path in "$SCRIPT_DIR" "$CHECKPOINT_DIR" "$MEMORY_DIR" "$SKILL_DIR"; do
    if [ ! -d "$dir_path" ]; then
        DIR_ERRORS=$((DIR_ERRORS + 1))
        echo "[$TIMESTAMP]   ❌ $dir_path: mevcut değil"
    fi
done

# ── 6. Disk Alanı Kontrolü ──
echo "[$TIMESTAMP] 💿 Disk alanı kontrol ediliyor..."
HERMES_SIZE=$(du -sb "$HOME/.hermes" 2>/dev/null | awk '{print $1}')
if [ "$HERMES_SIZE" -gt 5368709120 ]; then  # 5GB
    echo "🐛  ~/.hermes dizini 5GB'ı aştı ($((HERMES_SIZE / 1048576)) MB)"
else
    echo "[$TIMESTAMP]   ✅ ~/.hermes boyutu: $((HERMES_SIZE / 1024)) KB"
fi

# ── ÖZET ──
echo ""
echo "=========================================="
echo "  HEALTH CHECK ÖZETİ — $TIMESTAMP"
echo "=========================================="
echo "  Script syntax hataları: $SYNTAX_ERRORS"
echo "  Skill sorunları:        $SKILL_ERRORS"
echo "  Checkpoint durumu:      $([ $CHECKPOINT_OK -eq 1 ] && echo '✅ Geçerli' || echo '❌ Sorunlu')"
echo "  Bellek sorunları:       $MEMORY_ERRORS"
echo "  Dizin sorunları:        $DIR_ERRORS"

TOTAL_ERRORS=$((SYNTAX_ERRORS + SKILL_ERRORS + MEMORY_ERRORS + DIR_ERRORS))
echo "  Toplam hata:            $TOTAL_ERRORS"

if [ $TOTAL_ERRORS -eq 0 ] && [ $CHECKPOINT_OK -eq 1 ]; then
    echo "  ✅ SAĞLIK DURUMU: MÜKEMMEL"
elif [ $TOTAL_ERRORS -le 2 ]; then
    echo "  ⚠️  SAĞLIK DURUMU: KABUL EDİLEBİLİR"
else
    echo "  ❌ SAĞLIK DURUMU: KRİTİK — Onarım gerekli"
    echo "  Çözüm: python3 $SCRIPT_DIR/sureklilik_motoru.py --onar"
fi
echo "=========================================="
echo ""
echo "[$TIMESTAMP] 🏁 Health check tamamlandı."

# Log'a yaz
{
    echo "[$TIMESTAMP] SYNTAX=$SYNTAX_ERRORS SKILL=$SKILL_ERRORS CHECKPOINT=$CHECKPOINT_OK MEMORY=$MEMORY_ERRORS DIR=$DIR_ERRORS TOTAL=$TOTAL_ERRORS"
} >> "$LOG_DIR/health_check.log"

# Toplam hata varsa ve critical seviyeyi aştıysa uyarı
if [ $TOTAL_ERRORS -gt 3 ]; then
    echo "[$TIMESTAMP] ⚠️  KRİTİK: $TOTAL_ERRORS hata tespit edildi!" >> "$LOG_DIR/health_check.log"
fi

exit $TOTAL_ERRORS
