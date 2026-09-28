#!/bin/bash
# =============================================================================
# Hermes Idle Pulse — Cron Wrapper
# =============================================================================
# Faz 1: Otonom Background Loop
# Her 15 dakikada bir crontab'dan çağrılır.
# Sadece sorun varsa çıktı verir; her şey yolundaysa sessizdir.
#
# Kullanım:
#   ./idle_pulse.sh
#
# Cron'a ekleme:
#   */15 * * * * /opt/hermes/autonomy/phase-1-idle-pulse/idle_pulse.sh
# =============================================================================

set -o errexit   # Hata anında dur (ama python3 çıkışını yakalıyoruz)
set -o nounset   # Tanımsız değişken hatası
set -o pipefail  # Pipeline hatasını yakala

export PATH="/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin"
cd /opt/hermes/autonomy/phase-1-idle-pulse

python3 idle_pulse.py
exit "$?"
