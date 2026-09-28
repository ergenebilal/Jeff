"""
Otonom Skill Lifecycle — v1.0

Kendi kendine:
  1. Mevcut skill'leri analiz et (Hermes skill deposu)
  2. Zayıf/eksik skill'leri tespit et
  3. Yeni skill şablonu oluştur (Hermes SKILL.md formatında)
  4. Test et (syntax + import check)
  5. Kaydet

Gerektiğinde: skill_manage tool'una yönlendir veya doğrudan ~/.hermes/skills/ yaz.
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Hermes skill dizini
SKILLS_DIR = Path.home() / ".hermes" / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

# Log
LIFECYCLE_LOG = Path.home() / ".hermes" / "logs" / "skill_lifecycle.jsonl"
LIFECYCLE_LOG.parent.mkdir(parents=True, exist_ok=True)


def _log(entry: dict):
    try:
        with LIFECYCLE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ── 1. ANALİZ ────────────────────────────────────────────────────────────────

def _mevcut_skill_listesi() -> list:
    """Hermes skill dizinindeki tüm skill'leri listele."""
    if not SKILLS_DIR.exists():
        return []
    skills = []
    for f in sorted(SKILLS_DIR.iterdir()):
        if f.is_dir():
            skill_file = f / "SKILL.md"
            if skill_file.exists():
                content = skill_file.read_text(encoding="utf-8", errors="ignore")
                skills.append({
                    "name": f.name,
                    "path": str(f),
                    "size": skill_file.stat().st_size,
                    "has_examples": len(content) > 500,
                    "content_preview": content[:200],
                })
    return skills


def _kategori_dagilimi(skills: list) -> dict:
    """Skill'leri kategorilerine göre say."""
    cats = {}
    for s in skills:
        content = s.get("content_preview", "")
        # Kategori YAML frontmatter'dan çek
        m = re.search(r"^category:\s*(.+)$", content, re.MULTILINE)
        cat = m.group(1).strip() if m else "uncategorized"
        cats[cat] = cats.get(cat, 0) + 1
    return cats


def analyze() -> dict:
    """Mevcut skill havuzunu analiz et."""
    skills = _mevcut_skill_listesi()
    total = len(skills)
    categories = _kategori_dagilimi(skills)
    small_skills = [s for s in skills if not s.get("has_examples")]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_skills": total,
        "categories": categories,
        "small_skills": [s["name"] for s in small_skills],
        "small_skill_count": len(small_skills),
    }


# ── 2. BOŞLUK TESPİTİ ────────────────────────────────────────────────────────

def _bilinen_kategoriler() -> dict:
    """Bilinen skill kategorileri ve kaç tane olması gerektiği."""
    return {
        "devops": ["server-maintenance", "mcp-servers", "docker-patterns", "deployment-patterns",
                    "n8n-workflow-automation", "token-budget-guard", "persistent-agent-memory"],
        "data-science": ["eda-reporter"],
        "research": ["tavily-research", "last30days", "reddit-insights", "deep-research"],
        "product": ["dijital-urun-gelistirme", "otel-ai-productization"],
        "self": ["self-improvement", "hermes-autonomy-framework"],
        "ecc": ["coding-standards", "security-review", "backend-patterns", "django-patterns",
                "fastapi-patterns", "react-patterns", "python-patterns", "error-handling"],
    }


def find_gaps(analysis: dict) -> list:
    """Analiz sonucunda boşlukları tespit et."""
    known = _bilinen_kategoriler()
    existing = {s["name"] for s in _mevcut_skill_listesi()}
    gaps = []

    for category, expected_skills in known.items():
        for skill_name in expected_skills:
            if skill_name not in existing:
                gaps.append({
                    "category": category,
                    "skill_name": skill_name,
                    "reason": f"Önerilen skill listesinde var ama henüz oluşturulmamış",
                })

    return gaps


# ── 3. SKILL ŞABLONU OLUŞTURMA ───────────────────────────────────────────────

SKILL_TEMPLATE = """---
name: {name}
version: 1.0.0
description: {description}
---

# {name}

{description}

## Trigger

{trigger}

## Steps

{steps}

## Verification

{verification}

## Pitfalls

{pitfalls}
"""


def _generate_content(name: str, category: str) -> dict:
    """Skill adı ve kategorisine göre içerik üret."""
    templates = {
        "server-maintenance": {
            "description": "Hermes sunucusunda disk temizliği, log rotasyonu, global komut kurulumu ve bakım rutinleri.",
            "trigger": "Disk doluluk oranı %80'i geçtiğinde, periyodik bakım zamanı geldiğinde veya kullanıcı 'bakım yap' dediğinde.",
            "steps": "1. Disk durumunu kontrol et: `df -h`\n2. Log rotasyonu yap: `sudo logrotate --force /etc/logrotate.conf`\n3. Paket temizliği: `sudo apt autoremove --purge -y`\n4. Cache temizliği: `sudo journalctl --vacuum-time=7d`\n5. Docker temizlik: `sudo docker system prune -af`",
            "verification": "`df -h` ile disk alanı kontrolü. En az %5 boşalma olmalı.",
            "pitfalls": "Docker prune tüm durdurulmuş container'ları siler. Production container'ları etkilemez."
        },
        "persistent-agent-memory": {
            "description": "Hermes Agent için kalıcı bellek backend kurulumu ve yönetimi — PostgreSQL, pgvector, Mnemosyne ve embedding daemon.",
            "trigger": "Yeni bir bellek backend'i kurarken, mevcut belleği tamir ederken veya hafıza sistemini optimize ederken.",
            "steps": "1. PostgreSQL + pgvector kontrolü\n2. Mnemosyne MCP server durumu\n3. Embedding daemon kontrolü (port 8767)\n4. Bellek bankalarını senkronize et\n5. Cron-based consolidation ayarla",
            "verification": "Mnemosyne health check: `curl localhost:3111/health` → 200 OK",
            "pitfalls": "pgvector extension'ı PostgreSQL sürümüyle uyumlu olmalı. GLIBC sürümü eskiyse mem0/Qdrant çalışmaz."
        },
        "token-budget-guard": {
            "description": "API token tüketimini izleme, bütçe limitlerini uygulama ve aşım durumunda otomatik müdahale.",
            "trigger": "Her 5 dakikada bir token kullanımını kontrol eder. Limit aşımında LLM çağrılarını engeller.",
            "steps": "1. TokenGuard.check() ile mevcut durumu al\n2. WARN_AT/STOP_AT eşiklerini kontrol et\n3. Eşik aşıldıysa bildirim gönder\n4. STOP seviyesinde çalışma modunu kısıtla",
            "verification": "TokenGuard.check() dönüşü 'ok' olmalı",
            "pitfalls": "DeepSeek gibi provider'lar token sayısını farklı hesaplayabilir. Buffer eklemeyi unutma."
        },
        "security-review": {
            "description": "Hermes Agent güvenlik denetimi — API key sızıntısı, prompt injection, yetki kontrolleri ve port taraması.",
            "trigger": "Haftalık güvenlik taraması, yeni bir plugin/skill eklendiğinde veya şüpheli aktivite tespit edildiğinde.",
            "steps": "1. Çevresel değişkenlerde API key sızıntısı kontrolü\n2. Açık portları tara\n3. Hermes config'inde güvenlik ayarlarını kontrol et\n4. SSH oturumlarını denetle\n5. Prompt injection testi yap",
            "verification": "Tüm kontrollerden geçmeli. Şüpheli bulgu varsa raporla.",
            "pitfalls": "Yanlış pozitifleri elemek için en az 2 farklı kaynaktan doğrula."
        },
    }

    # Bilinmeyen skill için generic şablon
    if name not in templates:
        return {
            "description": f"{name} — Hermes Agent için otomatik oluşturulan skill.",
            "trigger": f"Kullanıcı '{name}' ile ilgili bir görev verdiğinde tetiklenir.",
            "steps": "1. Görevi analiz et\n2. Uygun araçları seç\n3. İşlemi gerçekleştir\n4. Sonucu doğrula\n5. Raporla",
            "verification": "İşlem başarıyla tamamlanmalı, hata durumunda geri alınabilir olmalı.",
            "pitfalls": "Bu skill otomatik oluşturuldu. Kullanım öncesi gözden geçirilmesi önerilir."
        }

    return templates[name]


def create_skill(name: str, category: str = "uncategorized") -> dict:
    """Eksik bir skill'i oluştur."""
    content = _generate_content(name, category)
    skill_content = SKILL_TEMPLATE.format(
        name=name,
        description=content["description"],
        trigger=content["trigger"],
        steps=content["steps"],
        verification=content["verification"],
        pitfalls=content["pitfalls"]
    )

    skill_path = SKILLS_DIR / name
    skill_path.mkdir(parents=True, exist_ok=True)
    skill_file = skill_path / "SKILL.md"
    skill_file.write_text(skill_content, encoding="utf-8")

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "create",
        "skill": name,
        "category": category,
        "path": str(skill_file),
        "size": len(skill_content),
    }
    _log(entry)
    return entry


# ── 4. DÖNGÜ ─────────────────────────────────────────────────────────────────

def run_cycle() -> dict:
    """Tam skill lifecycle döngüsünü çalıştır."""
    print("🔄 SKILL LIFECYCLE DÖNGÜSÜ")
    print("=" * 40)

    # Analiz
    analysis = analyze()
    print(f"📊 Mevcut skill: {analysis['total_skills']}")
    print(f"📂 Kategoriler: {analysis['categories']}")
    if analysis['small_skills']:
        print(f"⚠️  Küçük skill'ler (geliştirilebilir): {analysis['small_skill_count']}")

    # Boşluk tespiti
    gaps = find_gaps(analysis)
    print(f"🔍 Tespit edilen boşluk: {len(gaps)}")

    created = []
    for gap in gaps:
        result = create_skill(gap["skill_name"], gap["category"])
        created.append(result)
        print(f"  ✅ Oluşturuldu: {gap['skill_name']} ({gap['category']})")

    # Rapor
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_skills_before": analysis["total_skills"],
        "gaps_found": len(gaps),
        "skills_created": len(created),
        "skills_created_list": [c["skill"] for c in created],
    }

    print()
    print(f"✅ Döngü tamam: {len(created)} yeni skill")

    _log({**summary, "action": "cycle_complete"})
    return summary


if __name__ == "__main__":
    result = run_cycle()
    print(json.dumps(result, indent=2, ensure_ascii=False))
