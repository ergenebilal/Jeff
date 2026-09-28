#!/bin/bash
# Jeff 4.0 Sabah Brifingi — her gün 08:00
echo "🌅 **Jeff 4.0 Sabah Brifingi**"
echo ""

# Jeff 4.0 process durumu (supervisorctl ile)
echo "## ⚙️ Jeff 4.0 Süreçleri"
JEFF_STATUS=$(sudo supervisorctl status 2>&1 || echo "Jeff durum alınamadı")
echo '```'
echo "$JEFF_STATUS"
echo '```'
echo ""

# Sistem kaynakları
echo "## 💻 Sistem Kaynakları"
echo '```'
echo "Disk: $(df -h / | awk 'NR==2{print $3 "/" $2 " (" $5 ")"}')"
echo "RAM:  $(free -h | awk '/^Mem:/{print $3 "/" $2 " (" $4 " free)"}')"
echo "CPU:  $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1)% kullanım"
echo "Swap: $(free -h | awk '/^Swap:/{print $3 "/" $2}')"
echo "Uptime: $(uptime -p | sed 's/up //')"
echo '```'
echo ""

# Aktif cron'lar
echo "## 🔄 Aktif Cron"
CRON_COUNT=$(/home/hermes/.local/bin/hermes cron list 2>/dev/null | grep -c "✅\|scheduled" || echo "N/A")
echo "Toplam: $(/home/hermes/.local/bin/hermes cron list 2>/dev/null | grep -c 'job_id\|name' || echo "?") cron çalışıyor"
echo ""

echo "⏰ $(date '+%d.%m.%Y %H:%M')"
