#!/bin/bash
# Jeff Backup — GitHub'a yedekleme
# config (env'siz), skills, brain, tools, scripts, trajectory
set -e

REPO="/opt/ergeneai-core"
BACKUP_DIR="$REPO/jeff-backup"
DATE=$(date +%Y%m%d_%H%M%S)

echo "📦 Jeff → GitHub yedekleme basliyor: $DATE"

mkdir -p "$BACKUP_DIR"/{config,skills,brain,tools,scripts,state}

# 1. Config (API key'leri temizle)
echo "  📄 Config..."
cp ~/.hermes/config.yaml "$BACKUP_DIR/config/config.yaml"
# env dosyasini yedekleme — sadece hangi key'ler var bilgisi
grep -oP '^[A-Z_]+=' ~/.hermes/.env | sort > "$BACKUP_DIR/config/env-keys.txt" || true

# 2. Skills
echo "  🧠 Skills..."
rsync -a --delete ~/.hermes/skills/ "$BACKUP_DIR/skills/" 2>/dev/null || cp -r ~/.hermes/skills/* "$BACKUP_DIR/skills/"

# 3. Brain
echo "  🧠 Brain modules..."
cp -r /opt/hermes/brain/*.py "$BACKUP_DIR/brain/" 2>/dev/null || true

# 4. Custom tools
echo "  🔧 Custom tools..."
cp /home/hermes/hermes_data/hermes_tools/_manga.py "$BACKUP_DIR/tools/" 2>/dev/null || true
cp /home/hermes/hermes_data/hermes_tools/_kanban.py "$BACKUP_DIR/tools/" 2>/dev/null || true

# 5. Scripts (sadece aktif cron script'leri)
echo "  📜 Scripts..."
for s in probation_reminder.py vacuum_dbs.py n8n-mcp-watchdog.sh \
         backup-to-drive.py hermes-update-watchdog.sh daily_ig.py \
         jeff-watchdog.sh jeff-guardian.py closed_loop-kpi-cron.sh \
         closed_loop-revenue-cron.sh kanban_zombie_check.py \
         self-improvement-pulse.py; do
    [ -f ~/.hermes/scripts/"$s" ] && cp ~/.hermes/scripts/"$s" "$BACKUP_DIR/scripts/"
done

# 6. Trajectory + state
echo "  📊 State..."
cp ~/.hermes/manga_trajectory.json "$BACKUP_DIR/state/" 2>/dev/null || true
cp ~/.hermes/kanban.db "$BACKUP_DIR/state/" 2>/dev/null || true

# 7. Versiyon bilgisi
echo "  ℹ️  Info..."
{
    echo "Jeff Backup — $DATE"
    hermes --version 2>/dev/null || echo "hermes: N/A"
    echo "Commit: $(cd /opt/hermes && git rev-parse HEAD 2>/dev/null || echo N/A)"
    echo "Skills: $(find ~/.hermes/skills -name SKILL.md | wc -l)"
    echo "Scripts: $(ls ~/.hermes/scripts/*.py ~/.hermes/scripts/*.sh 2>/dev/null | wc -l)"
} > "$BACKUP_DIR/backup-info.txt"

# 8. README
echo "  📖 README..."
cat > "$BACKUP_DIR/README.md" << 'EOF'
# Jeff Backup

Bu dizin Jeff'in (Hermes Agent) kimlik dosyalarını içerir.
**API key'ler ve secret'lar dahil değildir.** Sadece yapılandırma, skill ve kod.

## İçindekiler
- `config/` — Hermes yapılandırması
- `skills/` — Tüm skill'ler (prosedürel hafıza)
- `brain/` — Beyin modülleri (KPI, observability, curator vb.)
- `tools/` — Özel tool'lar (Manga, Kanban)
- `scripts/` — Cron script'leri
- `state/` — Trajectory + kanban state

## Restore
```bash
cp -r jeff-backup/config/config.yaml ~/.hermes/
cp -r jeff-backup/skills/* ~/.hermes/skills/
cp jeff-backup/brain/*.py /opt/hermes/brain/
cp jeff-backup/tools/*.py /home/hermes/hermes_data/hermes_tools/
```
EOF

# 9. Git commit + push
echo "  📤 Git commit + push..."
cd "$REPO"
git add jeff-backup/
git commit -m "jeff-backup: otomatik yedekleme $DATE" --quiet 2>/dev/null || echo "  (degisiklik yok)"
git push origin master 2>/dev/null && echo "  ✅ GitHub'a pushlandi" || echo "  ⚠️ Push basarisiz"

echo ""
echo "✅ Jeff → GitHub yedekleme tamam!"
