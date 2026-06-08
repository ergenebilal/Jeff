#!/bin/bash
echo "=== JEFF RESTORE ==="
echo "1. Install Hermes Agent"
echo "2. Clone this repo: git clone https://github.com/ergenebilal/Jeff.git"
echo "3. Restore skills: cp -r backup-jeff/skills ~/.hermes/"
echo "4. Restore brain: cp -r backup-jeff/brain /opt/jeff-brain/"
echo "5. Restore Mnemosyne: psql -h localhost -U hermes -d hermes -f backup-jeff/mnemosyne.sql"
echo "6. Configure API keys manually"

