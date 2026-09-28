#!/bin/bash
# OpenCode native ile Hermes Watchdog - maliyet: $0
export PATH="/home/hermes/.hermes/node/bin:$PATH"
cd /home/hermes
opencode run --agent operator . "
Hermes Agent gelismelerini takip et:

1. Nous Research GitHub - yeni release var mi?
2. Hermes Agent dokumantasyonu - yeni ozellik?
3. Toplulukta onemli degisiklik?

Kisa raporu /home/hermes/hermes-watchdog/output-\$(date +%Y%m%d).md dosyasina yaz.
Sadece ONEMLI degisiklikleri listele.
"
