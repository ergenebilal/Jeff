#!/usr/bin/env bash
# Jeff Proactive Refresher — Context & Memory Refresher
# Jeff OS v1.1 Proactive | QA/Refresher Worker
# Her çalıştığında: cron sayımı + memory/SOUL özeti + yarın için 3 öncelik
set -uo pipefail

# ── Tarih ──────────────────────────────────────────────
TODAY=$(date +%Y-%m-%d)
TOMORROW=$(date -d "+1 day" +%Y-%m-%d 2>/dev/null || date -v+1d +%Y-%m-%d 2>/dev/null || echo "yarın")
TODAY_TR=$(date +"%d %B %Y" 2>/dev/null || echo "$TODAY")
TIME_NOW=$(date +"%H:%M")

# ── Yollar ─────────────────────────────────────────────
CRON_OUTPUT_DIR="$HOME/.hermes/cron/output"
SOUL_FILE="$HOME/.hermes/SOUL.md"
MEMORY_MD="$HOME/.hermes/MEMORY.md"
MEMORY_JSON="$HOME/.hermes/memory.json"
BRAIN_DIR="$HOME/.hermes/brain"
JOBS_JSON="$HOME/.hermes/cron/jobs.json"

# ── Renkler (opsiyonel) ────────────────────────────────
BOLD="\033[1m"
DIM="\033[2m"
RESET="\033[0m"
CYAN="\033[36m"
YELLOW="\033[33m"
GREEN="\033[32m"

# ╔═══════════════════════════════════════════════════════╗
# ║  1) BUGÜNKÜ CRON ÇIKTILARI                           ║
# ╚═══════════════════════════════════════════════════════╝
count_cron_today() {
    local count=0
    local files=()
    # Gerçek ls ile sayım (istenen komut)
    if ls "$CRON_OUTPUT_DIR"/*/*"$TODAY"* >/dev/null 2>&1; then
        count=$(ls "$CRON_OUTPUT_DIR"/*/*"$TODAY"* 2>/dev/null | wc -l)
        # trim spaces
        count=$(echo "$count" | tr -d ' ')
    else
        count=0
    fi
    echo "$count"
}

list_cron_jobs_today() {
    # Bugünkü dosyaları job bazında grupla
    if ls "$CRON_OUTPUT_DIR"/*/*"$TODAY"* >/dev/null 2>&1; then
        ls "$CRON_OUTPUT_DIR"/*/*"$TODAY"* 2>/dev/null | while read -r f; do
            job_id=$(basename "$(dirname "$f")")
            fname=$(basename "$f")
            # jobs.json'dan job adını çözmeye çalış
            job_name="$job_id"
            if [[ -f "$JOBS_JSON" ]]; then
                resolved=$(python3 -c "
import json,sys
try:
    d=json.load(open('$JOBS_JSON'))
    jobs=d.get('jobs',d) if isinstance(d,dict) else d
    for j in jobs:
        if j.get('id')=='$job_id':
            print(j.get('name','$job_id'))
            break
except: pass
" 2>/dev/null)
                [[ -n "$resolved" ]] && job_name="$resolved"
            fi
            echo "  • $job_name — $fname"
        done | sort | uniq -c | head -n 20
        # Özet: job başına kaç dosya
        echo ""
        echo "  --- job bazında ---"
        ls "$CRON_OUTPUT_DIR"/*/*"$TODAY"* 2>/dev/null | xargs -I{} dirname {} | sort | uniq -c | while read -r cnt dir; do
            jid=$(basename "$dir")
            jname="$jid"
            if [[ -f "$JOBS_JSON" ]]; then
                resolved=$(python3 -c "
import json
try:
    d=json.load(open('$JOBS_JSON'))
    jobs=d.get('jobs',d) if isinstance(d,dict) else d
    for j in jobs:
        if j.get('id')=='$jid':
            print(j.get('name','$jid'))
            break
except: pass
" 2>/dev/null)
                [[ -n "$resolved" ]] && jname="$resolved"
            fi
            echo "    $jname ($jid): $cnt çıktı"
        done
    else
        echo "  (bugün için cron çıktısı yok)"
    fi
}

CRON_COUNT=$(count_cron_today)

# Toplam job sayısı
TOTAL_JOBS="?"
if [[ -f "$JOBS_JSON" ]]; then
    TOTAL_JOBS=$(python3 -c "import json; d=json.load(open('$JOBS_JSON')); jobs=d.get('jobs',d) if isinstance(d,dict) else d; print(len(jobs))" 2>/dev/null || echo "?")
fi

# Son cron çıktısının içeriğinden kısa örnek (varsa)
LAST_CRON_SNIPPET=""
LAST_CRON_FILE=""
if ls "$CRON_OUTPUT_DIR"/*/*"$TODAY"* >/dev/null 2>&1; then
    LAST_CRON_FILE=$(ls -t "$CRON_OUTPUT_DIR"/*/*"$TODAY"* 2>/dev/null | head -n1)
    if [[ -n "$LAST_CRON_FILE" && -f "$LAST_CRON_FILE" ]]; then
        LAST_CRON_SNIPPET=$(head -n 5 "$LAST_CRON_FILE" 2>/dev/null | tr '\n' ' ' | cut -c1-120)
    fi
fi

# ╔═══════════════════════════════════════════════════════╗
# ║  2) MEMORY / SOUL DURUMU                             ║
# ╚═══════════════════════════════════════════════════════╝
SOUL_SUMMARY="(SOUL.md bulunamadı)"
if [[ -f "$SOUL_FILE" ]]; then
    # SOUL'dan Mission Map tablosunu çek
    SOUL_SUMMARY=$(grep -A 20 "Mission Map" "$SOUL_FILE" 2>/dev/null | head -n 15 | sed 's/^[[:space:]]*//')
    if [[ -z "$SOUL_SUMMARY" ]]; then
        SOUL_SUMMARY=$(head -n 30 "$SOUL_FILE" 2>/dev/null | tail -n 15)
    fi
    # Satır sayıları
    SOUL_LINES=$(wc -l < "$SOUL_FILE" 2>/dev/null | tr -d ' ')
    SOUL_MTIME=$(stat -c %y "$SOUL_FILE" 2>/dev/null | cut -d'.' -f1)
    [[ -z "$SOUL_MTIME" ]] && SOUL_MTIME=$(stat -f %Sm "$SOUL_FILE" 2>/dev/null)
fi

MEMORY_SUMMARY="(MEMORY.md bulunamadı)"
if [[ -f "$MEMORY_MD" ]]; then
    MEMORY_SUMMARY=$(head -n 60 "$MEMORY_MD" 2>/dev/null)
    MEMORY_MTIME=$(stat -c %y "$MEMORY_MD" 2>/dev/null | cut -d'.' -f1)
    [[ -z "$MEMORY_MTIME" ]] && MEMORY_MTIME=$(stat -f %Sm "$MEMORY_MD" 2>/dev/null)
    MEMORY_LINES=$(wc -l < "$MEMORY_MD" 2>/dev/null | tr -d ' ')
fi

# memory.json lesson sayısı
MEMORY_JSON_INFO=""
if [[ -f "$MEMORY_JSON" ]]; then
    MEMORY_JSON_INFO=$(python3 -c "
import json
try:
    d=json.load(open('$MEMORY_JSON'))
    print(f\"lesson_count={d.get('lesson_count',0)} | updated_at={d.get('updated_at','-')}\")
    for l in d.get('lessons',[])[:2]:
        print(f\"  - [{l.get('category')}] {l.get('lesson')} ({l.get('timestamp')})\")
except Exception as e:
    print(str(e))
" 2>/dev/null)
fi

# Brain dosyaları — gerçek okumalar
BRAIN_INFO=""
if [[ -d "$BRAIN_DIR" ]]; then
    BRAIN_INFO=$(cat <<BRAIN_EOF
  brain/mood_state.json: $(cat "$BRAIN_DIR/mood_state.json" 2>/dev/null | tr -d '\n' | cut -c1-80)
  brain/bilal_profile.json: $(cat "$BRAIN_DIR/bilal_profile.json" 2>/dev/null | python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('son_durum',{}).get('analiz',{}))" "$BRAIN_DIR/bilal_profile.json" 2>/dev/null | cut -c1-80)
  brain/semantic_knowledge.json: $(python3 -c "import json; d=json.load(open('$BRAIN_DIR/semantic_knowledge.json')); print(f\"{len(d.get('kavramlar',[]))} kavram\")" 2>/dev/null)
  brain/episodic son 1: $(tail -n1 "$BRAIN_DIR/episodic_memory.jsonl" 2>/dev/null | cut -c1-100)
  brain/decision_journal son 1: $(tail -n1 "$BRAIN_DIR/decision_journal.jsonl" 2>/dev/null | cut -c1-100)
BRAIN_EOF
)
fi

# Personal memory / agent state
AGENT_STATE_INFO=""
if [[ -f "$HOME/.hermes/agent_state.json" ]]; then
    AGENT_STATE_INFO=$(cat "$HOME/.hermes/agent_state.json" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -n 20)
fi

# ╔═══════════════════════════════════════════════════════╗
# ║  3) YARIN İÇİN 3 ÖNCELİK (dinamik)                    ║
# ╚═══════════════════════════════════════════════════════╝
# SOUL Mission Map'e ve cron durumuna göre öncelik üret
generate_priorities() {
    local p1="🔴 Instagram içerik üretimi — Post 2+ üretimini ilerlet (ErgeneAI editorial kalite, Akare eşiği)"
    local p2="🟡 Lead pipeline — 40 lead için email zenginleştirme + DM'e Hazır filtresi (IG+Tel kontrolü)"
    local p3="🟡 Jeff 2.0 — Cron health + Hizmet Motoru aktivasyonu (kanban dispatcher 30sn tick doğrulaması)"

    # Eğer bugünkü cron sayısı düşükse (sistem sessizse) önceliği ayarla
    if [[ "$CRON_COUNT" -lt 5 ]]; then
        p3="🔴 Cron sağlık kontrolü — Bugün sadece $CRON_COUNT çıktı, watchdog ve dispatcher loglarını incele"
    fi

    # Eğer dental-lead-gen bugün çalışmadıysa öner
    if ! ls "$CRON_OUTPUT_DIR"/*/*"$TODAY"* 2>/dev/null | grep -q "dental\|lead" 2>/dev/null; then
        # SOUL'da dental takibi varsa hatırlat — ama genel öncelik zaten lead pipeline
        true
    fi

    # Yarın gününe göre cron'ları hatırlat
    local dow
    dow=$(date +%u 2>/dev/null) # 1=Mon
    local tomorrow_dow=$(( dow % 7 + 1 ))
    case $tomorrow_dow in
        1) p3="🟡 Yarın Pazartesi — haftalık-dış-dünya-briefi + rakip-monitoring + dental-lead-gen tetiklenir, çıktıları QA et" ;;
        2) p3="🟡 Yarın Salı — dental-lead-gen günü, lead kalitesini denetle + outreach worker'ı besle" ;;
        4) p3="🟡 Yarın Perşembe — haftalık-dış-dünya-briefi günü, brief çıktısını Bilal'e özetle" ;;
        5) p3="🟡 Yarın Cuma — dental-lead-gen günü, haftalık lead raporunu hazırla" ;;
    esac

    echo "  1. $p1"
    echo "  2. $p2"
    echo "  3. $p3"
}

PRIORITIES=$(generate_priorities)

# ╔═══════════════════════════════════════════════════════╗
# ║  ÇIKTI — 🔔 JEFF PROAKTİF BİLDİRİM — REFRESHER       ║
# ╚═══════════════════════════════════════════════════════╝
echo ""
echo "🔔 JEFF PROAKTİF BİLDİRİM — REFRESHER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📅 Tarih: $TODAY ($TODAY_TR)  ⏰ $TIME_NOW  •  Yarın: $TOMORROW"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "━━━ 1) GÜN ÖZETİ — CRON ÇIKTILARI ━━━"
echo "  Toplam cron job: $TOTAL_JOBS"
echo "  Bugünkü çıktı sayısı ( $TODAY ): $CRON_COUNT dosya"
echo "    Komut: ls ~/.hermes/cron/output/*/*$TODAY* | wc -l → $CRON_COUNT"
if [[ -n "$LAST_CRON_FILE" ]]; then
    echo "  Son çıktı: $(basename "$(dirname "$LAST_CRON_FILE")")/$(basename "$LAST_CRON_FILE")"
    echo "  Önizleme: $LAST_CRON_SNIPPET"
fi
echo ""
# Detaylı liste (ilk 10)
echo "  Detay (ilk 10 dosya):"
list_cron_jobs_today | head -n 25
echo ""
echo "━━━ 2) MEMORY / SOUL DURUMU ━━━"
echo "  SOUL.md: ${SOUL_LINES:-?} satır | son güncelleme: ${SOUL_MTIME:-bilinmiyor}"
echo "  MEMORY.md: ${MEMORY_LINES:-?} satır | son güncelleme: ${MEMORY_MTIME:-bilinmiyor}"
echo ""
echo "  — SOUL Mission Map (özet) —"
echo "$SOUL_SUMMARY" | head -n 12 | sed 's/^/    /'
echo ""
echo "  — MEMORY.md (ilk 40 satır özet) —"
echo "$MEMORY_SUMMARY" | head -n 25 | sed 's/^/    /'
echo ""
if [[ -n "$MEMORY_JSON_INFO" ]]; then
    echo "  — memory.json —"
    echo "$MEMORY_JSON_INFO" | sed 's/^/    /'
    echo ""
fi
if [[ -n "$BRAIN_INFO" ]]; then
    echo "  — brain/ —"
    echo "$BRAIN_INFO" | sed 's/^/  /'
    echo ""
fi

echo "━━━ 3) YARIN İÇİN 3 ÖNCELİK ($TOMORROW) ━━━"
echo "$PRIORITIES"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Refresher tamamlandı — $TODAY $TIME_NOW | $CRON_COUNT cron çıktısı tarandı"
echo "   Kaynaklar: SOUL.md + MEMORY.md + memory.json + brain/* + cron/output"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
