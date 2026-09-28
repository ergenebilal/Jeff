#!/bin/bash
# Gateway restart tetikleyici — gateway process ağacı dışından (at/cron) koşturulur.
# Config'teki yeni default model (deepseek-v4-pro) yüklensin.
sleep 2
sudo systemctl restart hermes-gateway.service
echo "Restart komutu çalıştı, exit: $?"