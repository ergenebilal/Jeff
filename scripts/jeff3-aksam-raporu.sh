#!/bin/bash
# Jeff 4.0 Akşam Raporu — her gün 22:00
echo "🌙 **Jeff 4.0 Akşam Raporu**"
echo ""

# Jeff 4.0 process durumu (supervisorctl ile)
echo "## ⚙️ Jeff 4.0 Süreçleri"
JEFF_STATUS=$(sudo supervisorctl status 2>&1 || echo "Jeff durum alınamadı")
echo '```'
echo "$JEFF_STATUS"
echo '```'
echo ""

# Gün sonu sistem
echo "## 💻 Gün Sonu Sistem Durumu"
echo '```'
echo "Disk: $(df -h / | awk 'NR==2{print $3 "/" $2 " (" $5 ")"}')"
echo "RAM:  $(free -h | awk '/^Mem:/{print $3 "/" $2}')"
echo "Swap: $(free -h | awk '/^Swap:/{print $3 "/" $2}')"
echo '```'
echo ""

# Bugünkü audit log özeti
if [ -f /opt/hermes/audit/audit.log ]; then
    TODAY=$(date '+%Y-%m-%d')
    TOOL_COUNT=$(grep "$TODAY" /opt/hermes/audit/audit.log 2>/dev/null | wc -l)
    echo "## 📋 Bugünkü Aktivite"
    echo "Toplam tool çağrısı: $TOOL_COUNT"
    echo ""
fi

# Yarın için hatırlatmalar
echo "## 📌 Yarın"
NEXT_DAY=$(date -d '+1 day' '+%d.%m.%Y')
echo "Tarih: $NEXT_DAY"
echo ""

echo "⏰ $(date '+%d.%m.%Y %H:%M')"
