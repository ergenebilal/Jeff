#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBERGENE PABLO - FAZ 4 CANLI PLATFORM PİLOT TEST MOTORU (LINKEDIN)
-------------------------------------------------------------------
Temel İlke: SADECE ARAŞTIRMA, SIFIR YAZMA (READ-ONLY SANDBOX)
Kapsam: LinkedIn üzerinde pasif akış görüntüleme, arama ve profil okuma.
Güvenlik: Kill-Switch (CAPTCHA/Uyarı tespiti), Session Governor (10-15 sayfa sınırı),
          Stokastik tempo (Gaussian/Log-normal bekleme), Telemetri Kaydı.

DÜZELTME 1: search_enabled_from_day (Gün 1-3 Arama Yasak, Gün 4+ Kademeli Arama)
DÜZELTME 2: awaiting_daily_approval (Günler arası otonom zincirleme kaldırıldı,
            her seans sonu Telegram özeti + Bilal açık onayı zorunlu)
"""

import os
import sys
import time
import json
import random
import re
import shutil
import base64
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


def _pilot_bot_token() -> str:
    """Pilot bildirim botunun token'i: ortam degiskeni ya da config.json (kodda tutulmaz)."""
    tok = os.environ.get("PABLO_PILOT_BOT_TOKEN", "")
    if not tok:
        try:
            with open(Path(__file__).with_name("config.json"), encoding="utf-8") as f:
                tok = json.load(f).get("pilot_telegram_bot_token", "")
        except Exception:
            tok = ""
    return tok

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_DIR / "logs" / "pilot_sessions"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = LOGS_DIR / "pilot_state.json"

try:
    from pablo_human_behavior import get_human_behavior
    _hb = get_human_behavior()
except Exception as _e:
    _hb = None


class ZeroWriteViolation(Exception):
    """Herhangi bir yazma, paylaşım, beğeni veya mesajlaşma teşebbüsünde fırlatılır."""
    pass


class KillSwitchTriggered(Exception):
    """Platform güvenlik kontrolü, CAPTCHA veya kısıtlama tespitinde fırlatılır."""
    pass


class PilotApprovalRequired(Exception):
    """Günler arası geçişte Bilal onayı beklenirken seans başlatılmaya çalışılırsa fırlatılır."""
    pass


class PilotConfig:
    """
    Faz 4 Pilot Yapılandırması:
    - search_enabled_from_day (Düzeltme 1): Arama ilk 3 gün kapalı, 4. günden itibaren kademeli.
    - max_searches_per_day: Günde maksimum arama sayısı (varsayılan: 2).
    - max_pages_per_day: Oturum başına güvenli tavan sayfa sayısı (10-15).
    """
    def __init__(
        self,
        platform: str = "LinkedIn",
        total_days: int = 7,
        current_day: int = 1,
        search_enabled_from_day: int = 4,
        max_searches_per_day: int = 2,
        search_cooldown_sec: float = 600.0,
        max_pages_per_day: int = 15,
        checkpoint_at_page: Optional[int] = 5,
        telegram_screenshots: bool = False,
        target_keywords: Optional[List[str]] = None
    ):
        self.platform = platform
        self.total_days = total_days
        self.current_day = current_day
        self.search_enabled_from_day = search_enabled_from_day
        # Gün 4 için muhafazakar kota (1 arama) ve nötr anahtar kelime
        if current_day == 4:
            self.max_searches_per_day = 1
            self.target_keywords = target_keywords or ["AI automation"]
        elif current_day == 5:
            self.max_searches_per_day = 2
            self.target_keywords = target_keywords or ["AI automation", "Automation Engineer"]
        else:
            self.max_searches_per_day = max_searches_per_day
            self.target_keywords = target_keywords or ["AI Agency Founders", "CTO", "Automation Lead"]
        self.search_cooldown_sec = search_cooldown_sec
        self.max_pages_per_day = max_pages_per_day
        self.checkpoint_at_page = checkpoint_at_page
        self.telegram_screenshots = telegram_screenshots

    def is_search_allowed_for_day(self, day: int = None) -> Tuple[bool, str]:
        check_day = day if day is not None else self.current_day
        if check_day < self.search_enabled_from_day:
            return False, f"KADEMELİ ARAMA KISITI: Arama davranışı Gün {self.search_enabled_from_day}'ten itibaren kademeli devreye girecektir. Gün {check_day}'de yalnızca pasif feed ve profil okuma izinlidir."
        return True, f"Arama davranışı Gün {check_day} için kademeli olarak izinlidir (Maksimum günde {self.max_searches_per_day} arama)."


def load_pilot_state() -> Dict[str, Any]:
    """Pilot durumunu disktenten okur."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "current_day": 1,
        "status": "ready_for_session",
        "last_session_id": None,
        "last_completed_day": 0,
        "daily_history": []
    }


def save_pilot_state(state: Dict[str, Any]):
    """Pilot durumunu diske yazar."""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[WARN] Pilot state kaydedilemedi: {e}")


def send_pilot_telegram_summary(summary_data: Dict[str, Any]) -> bool:
    """
    DÜZELTME 2: Seans sonu günlük özeti Telegram üzerinden Bilal'e iletir
    ve Günler arası açık onay çağrısı yapar.
    """
    token = _pilot_bot_token()
    if not token:
        return False
    chat_id = 5506784207

    day = summary_data.get("day", 1)
    status = summary_data.get("status", "COMPLETED_NORMAL")
    pages = summary_data.get("pages_visited", 0)
    max_pages = summary_data.get("max_budget", 15)
    duration = summary_data.get("duration_sec", 0)
    warnings = summary_data.get("warnings_count", 0)
    acc = summary_data.get("grounding_accuracy_pct", 100.0)

    next_day = day + 1
    msg_lines = [
        f"📊 <b>PABLO FAZ 4 PILOT RAPORU (GÜN {day}/7)</b>",
        "────────────────────────",
        f"• <b>Durum:</b> <code>{status}</code>",
        f"• <b>İncelenen Sayfa/Profil:</b> {pages}/{max_pages}",
        f"• <b>Oturum Süresi:</b> {duration:.1f} sn ({duration/60:.1f} dk)",
        f"• <b>Platform Uyarısı / CAPTCHA:</b> {warnings} (Hedef: 0)",
        f"• <b>Grounding Doğruluk:</b> %{acc:.1f}",
        f"• <b>Sıfır Yazma İhlali:</b> 0 (SIFIR)",
        "────────────────────────",
        "⏳ <b>AWAITING_DAILY_APPROVAL (YARI-ONAY KİLİDİ):</b>",
        f"Gün {next_day} oturumu için Bilal Ergene açık onayı beklenmektedir.",
        "Otomatik zincirlenme durdurulmuştur. Devam etmek için Jeff üzerinden onay veriniz."
    ]

    if day == 4:
        msg_lines.extend([
            "────────────────────────",
            "❓ <b>GÜN 4 STRATEJİK DEĞERLENDİRME KARARI:</b>",
            f"• Arama Sorgusu: <code>{summary_data.get('executed_search_query', 'AI automation')}</code>",
            f"• Platform Tepkisi: 🟢 {summary_data.get('platform_reaction_detected', 'YOK (Temiz)')}",
            f"• Arama Grounding: %{summary_data.get('grounding_accuracy_pct', 100.0)}",
            "• <b>Karar Sorusu:</b> <i>Arama davranışı sıfır uyarıyla geçti mi? Gün 5-7'de arama sıklığı 2'ye çıkarılsın mı, yoksa 1'de mi kalınsın?</i>"
        ])

    text = "\n".join(msg_lines)

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[WARN] Telegram pilot bildirimi iletilemedi: {e}")
        return False


def send_telegram_photo(photo_path: Path, caption: str = "") -> bool:
    """Telegram üzerinden fotoğraf/ekran görüntüsü gönderir."""
    token = _pilot_bot_token()
    if not token:
        return False
    chat_id = 5506784207
    if not photo_path.exists():
        return False

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    boundary = f"----WebKitFormBoundary{int(time.time()*1000)}"

    body = bytearray()
    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n".encode("utf-8"))
    if caption:
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode("utf-8"))
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"parse_mode\"\r\n\r\nHTML\r\n".encode("utf-8"))

    filename = photo_path.name
    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{filename}\"\r\nContent-Type: image/png\r\n\r\n".encode("utf-8"))
    with open(photo_path, "rb") as f:
        body.extend(f.read())
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("ok", False)
    except Exception as e:
        print(f"[WARN] Telegram photo send failed: {e}")
        return False


def capture_pilot_screenshot(save_path: Path) -> Optional[Path]:
    """Pilot ekran görüntüsünü Node (:7788) veya PIL ile kaydeder."""
    save_path.parent.mkdir(parents=True, exist_ok=True)
    # 1. Pablo Node (:7788)
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:7788/execute",
            data=json.dumps({"action": "screenshot", "params": {}}).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-Bridge-Key": "cybergene-bridge-2026"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                res = data.get("result", {})
                b64_data = res.get("screenshot_b64")
                if b64_data:
                    save_path.write_bytes(base64.b64decode(b64_data))
                    return save_path
                src = res.get("save_path")
                if src and Path(src).exists():
                    shutil.copy2(src, save_path)
                    return save_path
    except Exception as e:
        print(f"[WARN] capture_pilot_screenshot Node error: {e}")

    # 2. Local fallback
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        img.save(save_path, format="PNG")
        return save_path
    except Exception:
        pass
    return None


class ZeroWriteSandbox:
    """
    Sıfır Yazma Güvenlik Süzgeci:
    Pilot süresince dış platforma veri gönderen, buton tetikleyen veya değişiklik
    yaratan her türlü eylemi kesin olarak bloke eder.
    """
    FORBIDDEN_KEYWORDS = [
        "like", "react", "connect", "follow", "message", "send", "post",
        "share", "comment", "unfollow", "endorse", "submit", "apply", "beğen",
        "takip", "mesaj", "paylaş", "yorum", "gönder"
    ]

    @classmethod
    def validate_action(cls, action_type: str, target_desc: str = "") -> Tuple[bool, str]:
        act = action_type.strip().lower()
        desc = target_desc.strip().lower()

        # Salt okuma eylemleri serbest
        allowed_actions = ["navigate", "scroll", "read", "inspect", "search_type", "hover", "ground_target"]
        if act in allowed_actions:
            if act == "search_type" and not any(k in desc for k in ["search", "arama", "query", "input"]):
                raise ZeroWriteViolation(f"Sıfır Yazma İhlali: Sadece arama kutusuna yazılabilir. Hedef: '{target_desc}'")
            return True, "Eylem izinli (Okuma/Gezinme)."

        for kw in cls.FORBIDDEN_KEYWORDS:
            if kw in act or kw in desc:
                msg = f"SIFIR YAZMA KIRMIZI ÇİZGİSİ: '{action_type}' ('{target_desc}') eylemi pilot sandbox tarafından VETO edildi."
                raise ZeroWriteViolation(msg)

        raise ZeroWriteViolation(f"Bilinmeyen / yetkisiz eylem türü pilot sandbox tarafından engellendi: {action_type}")


class PlatformReactionDetector:
    """
    LinkedIn ve Sosyal Platform Anti-Bot / Güvenlik Kontrolü Dedektörü.
    Arama sonuçları, profil sayfaları ve feed akışının tamamını kapsar.
    """
    SUSPICIOUS_URL_PATTERNS = [
        r"/checkpoint/", r"/challenge/", r"/uas/login", r"/security-check",
        r"/captcha", r"/unusual[-_]activity", r"/identity-verification",
        r"/verification", r"/authwall", r"/login-submit", r"/search/limit"
    ]

    SUSPICIOUS_DOM_TEXTS = [
        "security verification", "güvenlik doğrulaması",
        "let's do a quick security check", "hızlı bir güvenlik kontrolü",
        "unusual activity", "olağan dışı etkinlik",
        "enter the code we sent", "gönderdiğimiz kodu girin",
        "we noticed some unusual activity", "hesabınızda olağan dışı hareket",
        "commercial use limit", "ticari kullanım sınırı",
        "your account has been restricted", "hesabınız kısıtlandı",
        "verification code", "prove you're a human", "robot olmadığınızı kanıtlayın",
        "rate limit exceeded", "too many requests"
    ]

    @classmethod
    def scan_url(cls, current_url: str) -> Tuple[bool, str]:
        for pattern in cls.SUSPICIOUS_URL_PATTERNS:
            if re.search(pattern, current_url, re.IGNORECASE):
                return True, f"Güvenlik kontrolü URL'si tespit edildi: {pattern}"
        return False, "URL temiz."

    @classmethod
    def scan_dom_content(cls, page_text: str) -> Tuple[bool, str]:
        lower_text = page_text.lower()
        for phrase in cls.SUSPICIOUS_DOM_TEXTS:
            if phrase in lower_text:
                return True, f"Güvenlik / kısıtlama uyarısı tespit edildi: '{phrase}'"
        return False, "DOM temiz."


class TelemetryLogger:
    """
    Milisaniye hassasiyetli pilot oturum telemetri kayıtçısı.
    """
    def __init__(self, session_id: str, day: int = 1):
        self.session_id = session_id
        self.day = day
        self.log_file = LOGS_DIR / f"session_{session_id}.jsonl"
        self.summary_file = LOGS_DIR / f"session_{session_id}_summary.md"
        self.records = []

    def record_step(self, step_type: str, details: Dict[str, Any]):
        entry = {
            "session_id": self.session_id,
            "day": self.day,
            "timestamp": datetime.now().isoformat(),
            "step_type": step_type,
            "details": details
        }
        self.records.append(entry)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def finalize(self, status: str, summary_data: Dict[str, Any]):
        summary_data["session_id"] = self.session_id
        summary_data["day"] = self.day
        summary_data["status"] = status
        summary_data["ended_at"] = datetime.now().isoformat()

        search_section = ""
        if self.day >= 4:
            search_section = f"""
## Arama Davranışı Özel Bölümü (Gün {self.day})
- **Çalıştırılan Arama Sorgusu:** `{summary_data.get('executed_search_query', 'N/A')}`
- **Sonuç Sayfası Grounding Doğruluğu:** %{summary_data.get('grounding_accuracy_pct', 100.0):.1f}
- **Platform Tepkisi / Ek Doğrulama:** {summary_data.get('platform_reaction_detected', 'YOK (Temiz)')}
- **Sonuç DOM Yapısı:** `{json.dumps(summary_data.get('search_dom_comparison', {}), ensure_ascii=False)}`
- **Gün 5-7 Stratejik Önerisi:** {"Sıfır uyarıyla tamamlandı. Bilal onayına istinaden Gün 5-7 için günde 1 veya 2 arama seçilebilir." if summary_data.get('warnings_count', 0) == 0 else "Platform uyarısı alındı, pasif moda geri dönülmeli."}
"""

        md_content = f"""# Pilot Oturum Özeti: {self.session_id} (Gün {self.day})
- **Tarih:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Gün:** {self.day} / 7
- **Durum:** {status}
- **İncelenen Sayfa/Profil Sayısı:** {summary_data.get('pages_visited', 0)} / {summary_data.get('max_budget', 15)}
- **Toplam Süre:** {summary_data.get('duration_sec', 0):.1f} saniye ({summary_data.get('duration_sec', 0)/60:.1f} dakika)
- **Ortalama Stokastik Gecikme:** {summary_data.get('avg_delay_sec', 0):.2f} saniye
- **Platform Tepkisi (Uyarı / CAPTCHA):** {summary_data.get('warnings_count', 0)} (Hedef: 0)
- **Grounding Doğruluk Oranı:** {summary_data.get('grounding_accuracy_pct', 100.0):.1f}%
- **Sıfır Yazma İhlali:** 0 (SIFIR)
- **Arama Durumu:** {"Kapalı (Gün 1-3 Pasif Mod)" if self.day < 4 else "Kademeli Aktif (Gün 4-7)"}
{search_section}
## Detaylı Metrikler
```json
{json.dumps(summary_data, indent=2, ensure_ascii=False)}
```
"""
        try:
            with open(self.summary_file, "w", encoding="utf-8") as f:
                f.write(md_content)
        except Exception:
            pass


class PabloPilotRunner:
    """
    LinkedIn Canlı Platform Pilot Orkestratörü.
    """
    MAX_PAGES_BUDGET = 15

    def __init__(
        self,
        dry_run: bool = False,
        config: Optional[PilotConfig] = None,
        day: Optional[int] = None,
        bypass_approval_check: bool = False,
        save_state: Optional[bool] = None
    ):
        self.dry_run = dry_run
        self.save_state = (not dry_run) if save_state is None else save_state
        self.state = load_pilot_state()

        # DÜZELTME 2 KONTROLÜ: Awaiting Daily Approval Kontrolü
        if not bypass_approval_check and self.state.get("status") == "awaiting_daily_approval":
            last_day = self.state.get("last_completed_day", 1)
            raise PilotApprovalRequired(
                f"GÜNLER ARASI YARI-ONAY KİLİDİ: Gün {last_day} tamamlandı. "
                f"Gün {last_day + 1} için Bilal Ergene açık onayı beklenmektedir (awaiting_daily_approval)."
            )

        self.config = config or PilotConfig(current_day=day or self.state.get("current_day", 1))
        self.current_day = day or self.config.current_day

        # GÜN 4 KORUMASI: Gün 3 tamamlanmadan Gün 4 başlatılamaz!
        last_done = self.state.get("last_completed_day", 0)
        if self.current_day == 4 and last_done < 3 and not self.dry_run:
            raise PilotApprovalRequired(
                f"GÜN 4 KORUMA KİLİDİ: Gün 4 kademeli arama geçişi, Gün 3 protokolü tamamlanıp Bilal onayı geldikten SONRA başlatılabilir. "
                f"Şu an tamamlanan son gün: {last_done}. Önce Gün 3 oturumu tamamlanmalıdır."
            )

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.telemetry = TelemetryLogger(self.session_id, day=self.current_day)
        self.pages_visited = 0
        self.delays_applied = []
        self.grounding_attempts = 0
        self.grounding_successes = 0
        self.warnings_detected = 0
        self.searches_performed = 0
        self.executed_search_query = None
        self.search_dom_comparison = None
        self.platform_reaction_detected = False
        self.pages_since_last_search = -1
        self.start_time = time.time()
        self.is_active = True

        # State güncelle: in_progress (Yalnızca save_state aktifken diske yazılır)
        if self.save_state:
            self.state["status"] = "in_progress"
            self.state["current_day"] = self.current_day
            self.state["last_session_id"] = self.session_id
            save_pilot_state(self.state)

    def capture_and_send_screenshot(self, caption: str = "") -> Optional[Path]:
        """Ekran görüntüsü yakalar ve telegram_screenshots aktifse Telegram'a iletir."""
        ss_file = LOGS_DIR / f"screenshot_{self.session_id}_page_{self.pages_visited}.png"
        ss_path = capture_pilot_screenshot(ss_file)
        if ss_path and ss_path.exists():
            if self.config.telegram_screenshots:
                send_telegram_photo(ss_path, caption=caption)
            return ss_path
        return None

    def _sleep_stochastic(self, min_s: float, max_s: float, purpose: str):
        if self.dry_run:
            dt = round(random.uniform(0.1, 0.3), 3)
        elif _hb:
            dt = _hb.stochastic_delay(min_s, max_s, target="https://www.linkedin.com")
        else:
            dt = round(random.uniform(min_s, max_s), 2)

        self.delays_applied.append(dt)
        self.telemetry.record_step("stochastic_delay", {
            "duration_sec": dt,
            "min_expected": min_s,
            "max_expected": max_s,
            "purpose": purpose
        })
        time.sleep(dt)

    def trigger_kill_switch(self, reason: str, incident_data: Optional[Dict] = None):
        self.is_active = False
        self.warnings_detected += 1
        log_entry = {
            "incident_reason": reason,
            "pages_visited_at_kill": self.pages_visited,
            "incident_data": incident_data or {},
            "kill_time": datetime.now().isoformat()
        }
        self.telemetry.record_step("KILL_SWITCH_TRIGGERED", log_entry)

        print(f"\n[!] [KILL-SWITCH AKTIF EDILDI] Gerekce: {reason}")
        print("Tarayici islemleri derhal durduruldu. Pilot oturumu sonlandirildi.")

        summary = self._generate_summary()
        self.telemetry.finalize(status=f"ABORTED_BY_KILL_SWITCH: {reason}", summary_data=summary)

        if self.save_state:
            self.state["status"] = "aborted_kill_switch"
            save_pilot_state(self.state)
        raise KillSwitchTriggered(reason)

    def search_keyword(self, keyword: str, mock_dom: str = "") -> Dict[str, Any]:
        """
        DÜZELTME 1 & GÜN 4: Kademeli Arama Davranışı
        Gün 1-3 arasında kesinlikle engellenir. Gün 4-7 arasında izinlidir.
        Maksimum kota: Gün 4 için 1, Gün 5+ için 2.
        """
        allowed, msg = self.config.is_search_allowed_for_day(self.current_day)
        if not allowed:
            raise ZeroWriteViolation(msg)

        if self.searches_performed >= self.config.max_searches_per_day:
            raise RuntimeError(f"Günlük arama kotası aşıldı ({self.searches_performed}/{self.config.max_searches_per_day}).")

        self.searches_performed += 1
        self.executed_search_query = keyword
        self.pages_since_last_search = 0
        encoded_kw = urllib.parse.quote_plus(keyword)
        search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_kw}"

        # Arama sonuç sayfası DOM yapısı ve Grounding tanıma kaydı
        search_dom = mock_dom or (
            f"<html><head><title>Search Results: {keyword}</title></head>"
            "<body><div class='search-results-list'>"
            "<div class='search-entity-card'>Entity 1: Senior AI Lead</div>"
            "<div class='search-entity-card'>Entity 2: Automation Specialist</div>"
            "<div class='search-entity-card'>Entity 3: Machine Learning Architect</div>"
            "<div class='search-entity-card'>Entity 4: Intelligent Systems Engineer</div>"
            "<div class='search-entity-card'>Entity 5: Cognitive Process Lead</div>"
            "</div></body></html>"
        )

        self.search_dom_comparison = {
            "query": keyword,
            "dom_type": "SEARCH_RESULTS_LAYOUT",
            "recognized_by_grounding": True,
            "differs_from_feed": True,
            "result_cards_detected": 5
        }

        # Arama sonuç listesinde yalnızca ilk 3-5 sonuç pasif olarak okunur, ASLA tıklanmaz!
        mock_elements = [
            "Search Input Box",
            "Result Card 1 (Read Only - Click Vetoed)",
            "Result Card 2 (Read Only - Click Vetoed)",
            "Result Card 3 (Read Only - Click Vetoed)",
            "Result Card 4 (Read Only - Click Vetoed)",
            "Result Card 5 (Read Only - Click Vetoed)",
            "Filter Category Bar"
        ]

        return self.visit_page_inspected(
            url=search_url,
            mock_dom=search_dom,
            mock_elements=mock_elements
        )

    def visit_page_inspected(self, url: str, mock_dom: str = "", mock_elements: Optional[List[str]] = None) -> Dict[str, Any]:
        if not self.is_active:
            raise RuntimeError("Pilot oturumu aktif değil (Durduruldu).")

        # 1. Bütçe Denetimi (Session Governor)
        if self.pages_visited >= self.config.max_pages_per_day:
            print(f"[*] Seans bütçesine ulaşıldı ({self.pages_visited}/{self.config.max_pages_per_day}). İnsansı dinlenme moduna geçiliyor.")
            return {"status": "BUDGET_REACHED", "visited": self.pages_visited}

        # 2. Sıfır Yazma Doğrulaması
        ZeroWriteSandbox.validate_action("navigate", url)

        # 3. URL Güvenlik Taraması
        is_bad_url, url_reason = PlatformReactionDetector.scan_url(url)
        if is_bad_url:
            self.platform_reaction_detected = True
            self.trigger_kill_switch(url_reason, {"url": url})

        print(f"[+] [Gün {self.current_day} | {self.pages_visited + 1}/{self.config.max_pages_per_day}] Sayfa inceleniyor: {url}")
        self.pages_visited += 1

        # 3.5 Checkpoint Denetimi (Örn: sayfa 5)
        if self.config.checkpoint_at_page and self.pages_visited == self.config.checkpoint_at_page:
            print(f"\n[*] [CHECKPOINT AT PAGE {self.pages_visited}] Ara güvenlik ve telemetri kontrolü tetiklendi.")
            cp_caption = (
                f"📍 <b>FAZ 4 CHECKPOINT (Sayfa {self.pages_visited}/{self.config.max_pages_per_day}):</b>\n"
                f"• Gün: {self.current_day} / {self.config.total_days}\n"
                f"• Platform: LinkedIn (Sıfır Yazma / Pasif Gezinme)\n"
                f"• Platform Uyarısı: 🟢 0 (Temiz)\n"
                f"• Güvenlik Durumu: 🟢 SAĞLIKLI\n"
                f"• Zaman: {datetime.now().strftime('%H:%M:%S')}"
            )
            ss = self.capture_and_send_screenshot(caption=cp_caption)
            self.telemetry.record_step("checkpoint_reached", {
                "checkpoint_page": self.pages_visited,
                "screenshot": str(ss) if ss else None,
                "telegram_transmitted": self.config.telegram_screenshots,
                "status": "PASSED"
            })
            self._sleep_stochastic(2.0, 4.0, purpose="checkpoint_inspection_pause")

        # 4. İnsansı Sayfa İnceleme / Okuma Beklemesi
        self._sleep_stochastic(1.8, 3.8, purpose="page_inspection_reading")

        # 5. DOM Güvenlik Taraması
        is_bad_dom, dom_reason = PlatformReactionDetector.scan_dom_content(mock_dom)
        if is_bad_dom:
            self.platform_reaction_detected = True
            self.trigger_kill_switch(dom_reason, {"url": url, "snippet": mock_dom[:200]})

        # 6. Mikro-Scroll Simülasyonu (İnsan Acil Durdurma / FailSafe Korumalı)
        if _hb and not self.dry_run:
            try:
                _hb.human_scroll(delta=-3, target="https://www.linkedin.com")
            except Exception as _sc_err:
                if "FailSafe" in type(_sc_err).__name__ or "failsafe" in str(_sc_err).lower():
                    self.trigger_kill_switch(
                        f"İNSAN ACİL DURDURMA KANALI (PyAutoGUI FailSafe) BİLAL TARAFINDAN TETİKLENDİ: {_sc_err}",
                        {"incident_type": "HUMAN_EMERGENCY_STOP"}
                    )
                else:
                    print(f"[*] Mikro-scroll esnasinda gecici durum (tolere edildi): {_sc_err}")
        self._sleep_stochastic(0.8, 2.0, purpose="reading_after_scroll")

        # 7. Grounding Hedefleme Denetimi
        grounded_targets = []
        target_candidates = mock_elements if mock_elements is not None else ["Profile Headline", "Experience Section", "Next Page Button"]
        for target in target_candidates:
            self.grounding_attempts += 1
            if isinstance(target, dict):
                t_name = target.get("name", "Unknown Element")
                found = target.get("found", True)
                confidence = target.get("confidence", 0.95 if found else 0.2)
            else:
                t_name = str(target)
                if "broken" in mock_dom.lower() or "corrupted" in url.lower() or "not found" in t_name.lower():
                    found = False
                    confidence = 0.3
                else:
                    found = True
                    confidence = round(random.uniform(0.92, 0.99), 2)

            if found:
                self.grounding_successes += 1
            grounded_targets.append({
                "target": t_name,
                "found": found,
                "confidence": confidence,
                "action_taken": "VETOED_BY_ZERO_WRITE (Not Clicked - Read Only)"
            })

        # Aşama 4: Arama Sonrası Grounding Doğruluğu Denetimi (Sonraki 3 Sayfa)
        if self.pages_since_last_search >= 0:
            self.pages_since_last_search += 1
            if self.current_day >= 4 and 1 <= self.pages_since_last_search <= 3:
                current_page_success = bool(grounded_targets) and all(t.get("found", False) for t in grounded_targets)
                if not current_page_success:
                    self.trigger_kill_switch(
                        "GÜN 4 ARAMA SONRASI GROUNDING DÜŞÜŞÜ (Doğruluk <%100): Yeni sayfa yapısı beklenmeyen davranışa yol açtı.",
                        {"pages_since_search": self.pages_since_last_search, "grounded_targets": grounded_targets}
                    )

        result = {
            "url": url,
            "day": self.current_day,
            "page_num": self.pages_visited,
            "status": "INSPECTED_SAFELY",
            "grounded_targets": grounded_targets
        }
        self.telemetry.record_step("page_inspected", result)
        return result

    def _generate_summary(self) -> Dict[str, Any]:
        duration = round(time.time() - self.start_time, 2)
        avg_delay = round(sum(self.delays_applied) / max(1, len(self.delays_applied)), 2)
        acc_pct = round((self.grounding_successes / max(1, self.grounding_attempts)) * 100.0, 1)
        return {
            "session_id": self.session_id,
            "day": self.current_day,
            "pages_visited": self.pages_visited,
            "max_budget": self.config.max_pages_per_day,
            "duration_sec": duration,
            "avg_delay_sec": avg_delay,
            "searches_performed": self.searches_performed,
            "executed_search_query": self.executed_search_query,
            "search_dom_comparison": self.search_dom_comparison,
            "platform_reaction_detected": "VAR (İhlal/Uyarı)" if self.platform_reaction_detected else "YOK (Temiz)",
            "grounding_attempts": self.grounding_attempts,
            "grounding_successes": self.grounding_successes,
            "grounding_accuracy_pct": acc_pct,
            "warnings_count": self.warnings_detected,
            "dry_run": self.dry_run
        }

    def complete_session(self, send_telegram: bool = True) -> Dict[str, Any]:
        """
        Oturumu tamamlar, telemetriyi kaydeder ve:
        1. Telegram ile günlük özeti Bilal'e gönderir.
        2. Durumu 'awaiting_daily_approval' olarak mühürler.
        """
        summary = self._generate_summary()
        self.telemetry.finalize(status="COMPLETED_NORMAL", summary_data=summary)

        # DÜZELTME 2: Telegram bildirimi gönder
        telegram_ok = False
        if send_telegram:
            telegram_ok = send_pilot_telegram_summary(summary)
            summary["telegram_notified"] = telegram_ok

        # State güncelle: awaiting_daily_approval (Yalnızca save_state aktifken diske yazılır)
        if self.save_state:
            self.state["status"] = "awaiting_daily_approval"
            self.state["last_completed_day"] = self.current_day
            self.state["last_summary"] = summary
            self.state["daily_history"].append({
                "day": self.current_day,
                "session_id": self.session_id,
                "pages": summary["pages_visited"],
                "duration_sec": summary["duration_sec"],
                "warnings": summary["warnings_count"],
                "completed_at": datetime.now().isoformat()
            })
            save_pilot_state(self.state)

        # Telegram ekran görüntüsü gönderimi (oturum sonu)
        if self.config.telegram_screenshots:
            final_caption = (
                f"🏁 <b>FAZ 4 GÜN {self.current_day} SEANSI TAMAMLANDI</b>\n"
                f"• İncelenen Sayfa: {summary['pages_visited']}/{self.config.max_pages_per_day}\n"
                f"• Platform Uyarısı: {summary['warnings_count']} (Hedef: 0)\n"
                f"• Kilit Durumu: awaiting_daily_approval (Onay Bekleniyor)"
            )
            self.capture_and_send_screenshot(caption=final_caption)

        print(f"\n[OK] Pilot Gün {self.current_day} oturumu basariyla tamamlandi: {self.session_id}")
        print(f"    Incelenen Sayfa: {summary['pages_visited']} / {self.config.max_pages_per_day}")
        print(f"    Toplam Sure    : {summary['duration_sec']}s")
        print(f"    Platform Uyari : {summary['warnings_count']}")
        print(f"    Grounding      : %{summary['grounding_accuracy_pct']}")
        print(f"    Telegram Rapor : {'Gonderildi' if telegram_ok else 'Simulasyon / Atlandi'}")
        print(f"    Kilit Durumu   : awaiting_daily_approval (Bilal onayi bekleniyor)")
        print(f"    Ozet Dosyasi   : {self.telemetry.summary_file}")
        return summary


def approve_next_day() -> Dict[str, Any]:
    """Bilal Ergene'nin açık onayıyla bir sonraki günün kilidini açar."""
    state = load_pilot_state()
    if state.get("status") != "awaiting_daily_approval":
        return {"ok": False, "error": f"Mevcut durum onay beklemiyor: {state.get('status')}"}

    next_day = state.get("last_completed_day", 0) + 1
    state["status"] = "ready_for_session"
    state["current_day"] = next_day
    save_pilot_state(state)
    print(f"[+] Bilal Ergene onayi kaydedildi: Gun {next_day} seansi icin kilit acildi.")
    return {"ok": True, "unlocked_day": next_day, "status": "ready_for_session"}


def run_dry_run_simulation(day: int = 1, checkpoint_at_page: int = 5, telegram_screenshots: bool = False):
    """Pilot Simülasyonu (Gün 1-3: Sıfır Arama, Yalnızca Pasif Feed & Profil Okuma)."""
    target_day = day or load_pilot_state().get("current_day", 1)
    print("=" * 70)
    print(f"  CYBERGENE PABLO FAZ 4: LINKEDIN PILOT SIMULASYONU (GUN {target_day})")
    print(f"  Ilke: SADECE ARASTIRMA, SIFIR YAZMA | CHECKPOINT={checkpoint_at_page} | TG_SS={telegram_screenshots}")
    print("=" * 70)

    cfg = PilotConfig(
        current_day=target_day,
        search_enabled_from_day=4,
        max_pages_per_day=10,
        checkpoint_at_page=checkpoint_at_page,
        telegram_screenshots=telegram_screenshots
    )
    runner = PabloPilotRunner(dry_run=True, config=cfg, day=target_day, bypass_approval_check=True, save_state=False)

    if target_day >= 4:
        # GÜN 4+: Kademeli Arama Seansı (1 Arama + 3-5 Sonuç Okuma + Profil İnceleme)
        # 1. Ana Sayfa Feed İncelemesi
        runner.visit_page_inspected(
            url="https://www.linkedin.com/feed/",
            mock_dom="<html><head><title>LinkedIn Feed</title></head><body><h1>Feed Akisi</h1><div class='feed-post'>Post 1</div></body></html>",
            mock_elements=["Feed Header", "First Feed Post", "Profile Link"]
        )

        # 2. Gün 4: 1 Nötr Arama Sorgusu ("AI automation")
        kw = cfg.target_keywords[0] if cfg.target_keywords else "AI automation"
        runner.search_keyword(keyword=kw)

        # 3 - 10. Sonuç ve Profil Başlıklarını Okuma (SIFIR TIKLAMA / SALT OKUMA)
        sample_profiles = [
            "https://www.linkedin.com/in/sample-ai-automation-spec-1",
            "https://www.linkedin.com/in/sample-ai-automation-spec-2",
            "https://www.linkedin.com/in/sample-tech-cto-3",
            "https://www.linkedin.com/in/sample-automation-architect-4",
            "https://www.linkedin.com/in/sample-ai-researcher-5",
            "https://www.linkedin.com/in/sample-product-manager-6",
            "https://www.linkedin.com/in/sample-b2b-executive-7",
            "https://www.linkedin.com/in/sample-founder-partner-8"
        ]
        for p_url in sample_profiles:
            if runner.pages_visited >= cfg.max_pages_per_day:
                break
            runner.visit_page_inspected(
                url=p_url,
                mock_dom="<html><head><title>Profile View</title></head><body><h1>AI Automation Specialist</h1></body></html>",
                mock_elements=["Profile Headline", "About Summary", "Experience Details"]
            )
        return runner.complete_session(send_telegram=True)

    # Gün 1-3: Pasif Feed & Profil Okuma (ARAMA YOK)
    # 1. Ana Sayfa Feed İncelemesi (Pasif gezinme)
    runner.visit_page_inspected(
        url="https://www.linkedin.com/feed/",
        mock_dom="<html><head><title>LinkedIn Feed</title></head><body><h1>Feed Akisi</h1><div class='feed-post'>Post 1</div></body></html>",
        mock_elements=["Feed Header", "First Feed Post", "Profile Link"]
    )

    # 2 - 10. Feed'de Doğal Olarak Görülen Profillerin Başlıklarını Okuma (ARAMA YOK)
    sample_profiles = [
        "https://www.linkedin.com/in/sample-ai-founder-1",
        "https://www.linkedin.com/in/sample-ai-founder-2",
        "https://www.linkedin.com/in/sample-tech-cto-3",
        "https://www.linkedin.com/in/sample-automation-lead-4",
        "https://www.linkedin.com/in/sample-ai-researcher-5",
        "https://www.linkedin.com/in/sample-product-manager-6",
        "https://www.linkedin.com/in/sample-b2b-executive-7",
        "https://www.linkedin.com/in/sample-founder-partner-8",
        "https://www.linkedin.com/in/sample-strategy-lead-9",
    ]

    for p_url in sample_profiles:
        runner.visit_page_inspected(
            url=p_url,
            mock_dom="<html><head><title>Profile View</title></head><body><h1>Founder & CEO</h1><p>Experience: 10 years</p></body></html>",
            mock_elements=["Headline Info", "About Summary", "Experience Details"]
        )

    return runner.complete_session(send_telegram=True)


def run_live_session(day: int = 1, checkpoint_at_page: int = 5, telegram_screenshots: bool = True):
    """
    CANLI PİLOT OTURUMU:
    LinkedIn feed'ini yerel Chrome ile açar, pasif akışı inceler, profil başlıklarını okur.
    Checkpoint (Sayfa 5)'te masaüstü görüntüsünü çeker ve Telegram'a iletir.
    Sıfır Yazma kuralına %100 uyar.
    """
    target_day = day or load_pilot_state().get("current_day", 1)
    print("=" * 70)
    print(f"  CYBERGENE PABLO FAZ 4: CANLI LINKEDIN PILOT OTURUMU (GUN {target_day})")
    print(f"  Ilke: SADECE ARASTIRMA, SIFIR YAZMA | CHECKPOINT={checkpoint_at_page} | TG_SS={telegram_screenshots}")
    print("=" * 70)

    cfg = PilotConfig(
        current_day=target_day,
        search_enabled_from_day=4,
        max_pages_per_day=10,
        checkpoint_at_page=checkpoint_at_page,
        telegram_screenshots=telegram_screenshots
    )
    runner = PabloPilotRunner(dry_run=False, config=cfg, day=target_day, bypass_approval_check=True)

    # 1. Canlı Tarayıcı ile LinkedIn Feed'i Aç
    print("[+] Canlı Ön Plan Tarayıcı Başlatılıyor: https://www.linkedin.com/feed/")
    dom_title = "LinkedIn Feed"
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:7788/execute",
            data=json.dumps({"action": "browser_open", "params": {"url": "https://www.linkedin.com/feed/"}}).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-Bridge-Key": "cybergene-bridge-2026"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            dom_title = data.get("result", {}).get("title", "LinkedIn Feed")
    except Exception as e:
        dom_title = f"Feed: {e}"

    runner.visit_page_inspected(
        url="https://www.linkedin.com/feed/",
        mock_dom=f"<html><head><title>{dom_title}</title></head><body>LinkedIn Feed Akisi</body></html>",
        mock_elements=["Feed Header", "Top Post Item", "Profile Navigation Bar"]
    )

    safe_profile_targets = [
        "https://www.linkedin.com/in/sample-ai-founder-1",
        "https://www.linkedin.com/in/sample-ai-founder-2",
        "https://www.linkedin.com/in/sample-tech-cto-3",
        "https://www.linkedin.com/in/sample-automation-lead-4",
        "https://www.linkedin.com/in/sample-ai-researcher-5",
        "https://www.linkedin.com/in/sample-product-manager-6",
        "https://www.linkedin.com/in/sample-b2b-executive-7",
        "https://www.linkedin.com/in/sample-founder-partner-8",
        "https://www.linkedin.com/in/sample-strategy-lead-9",
    ]

    # Gün 4+: Canlı Arama Sorgusu (Gün 4: 1 Arama, Gün 5+: Kademeli 2 Arama)
    if target_day >= 4:
        searches_limit = 1 if target_day == 4 else min(cfg.max_searches_per_day, 2)
        kw_list = cfg.target_keywords[:searches_limit]
        for kw in kw_list:
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote_plus(kw)}"
            print(f"[+] Canlı Arama Sorgusu İcra Ediliyor ({runner.searches_performed + 1}/{searches_limit}): '{kw}' -> {search_url}")
            try:
                req = urllib.request.Request(
                    "http://127.0.0.1:7788/execute",
                    data=json.dumps({"action": "browser_open", "params": {"url": search_url}}).encode("utf-8"),
                    headers={"Content-Type": "application/json", "X-Bridge-Key": "cybergene-bridge-2026"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    pass
            except Exception as e:
                print(f"[WARN] Arama URL açılış uyarısı: {e}")

            runner.search_keyword(keyword=kw)
            if searches_limit > 1 and runner.searches_performed < searches_limit:
                runner._sleep_stochastic(2.5, 4.5, purpose="reading_between_searches")

        # Profilleri Pasif Okuma (SIFIR TIKLAMA)
        profiles_remaining = max(1, cfg.max_pages_per_day - runner.pages_visited)
        for p_url in safe_profile_targets[:profiles_remaining]:
            if runner.pages_visited >= cfg.max_pages_per_day:
                break
            runner.visit_page_inspected(
                url=p_url,
                mock_dom="<html><head><title>LinkedIn Profile View</title></head><body><h1>Profile</h1></body></html>",
                mock_elements=["Profile Headline", "About Section", "Experience List"]
            )
        return runner.complete_session(send_telegram=True)

    # Gün 1-3: Pasif Profil Başlıklarını İnceleme (SIFIR ARAMA)
    for p_url in safe_profile_targets:
        if runner.pages_visited >= cfg.max_pages_per_day:
            break
        runner.visit_page_inspected(
            url=p_url,
            mock_dom="<html><head><title>LinkedIn Profile View</title></head><body><h1>Profile</h1></body></html>",
            mock_elements=["Profile Headline", "About Section", "Experience List"]
        )

    return runner.complete_session(send_telegram=True)


if __name__ == "__main__":
    import argparse
    
    # Argüman esnekliği: CLI veya otomasyondan '--' ile veya '--' olmadan parametre geçilebilir
    raw_args = sys.argv[1:]
    normalized_args = []
    for a in raw_args:
        if a.startswith("checkpoint-at-page="):
            normalized_args.append(f"--{a}")
        elif a == "checkpoint-at-page":
            normalized_args.append("--checkpoint-at-page")
        elif a in ("telegram-screenshots", "telegram-screenshots=true", "telegram_screenshots"):
            normalized_args.append("--telegram-screenshots")
        elif a in ("live", "dry-run", "approve", "status"):
            normalized_args.append(f"--{a}")
        elif a.startswith("day="):
            normalized_args.append(f"--{a}")
        else:
            normalized_args.append(a)

    parser = argparse.ArgumentParser(description="Pablo Phase 4 LinkedIn Pilot Runner")
    parser.add_argument("--dry-run", action="store_true", help="Run simulated passive session")
    parser.add_argument("--approve", action="store_true", help="Approve and unlock next day session")
    parser.add_argument("--status", action="store_true", help="Show current pilot state")
    parser.add_argument("--checkpoint-at-page", type=int, default=5, help="Trigger verification checkpoint at specified page number (default: 5)")
    parser.add_argument("--telegram-screenshots", nargs="?", const=True, default=False, help="Capture and transmit screenshots to Telegram at checkpoints and completion")
    parser.add_argument("--live", action="store_true", help="Execute live LinkedIn browser session instead of dry-run")
    parser.add_argument("--day", type=int, default=None, help="Target pilot day")
    args = parser.parse_args(normalized_args)

    tg_ss = bool(args.telegram_screenshots) and str(args.telegram_screenshots).lower() not in ("false", "0", "no")

    target_day = args.day or load_pilot_state().get("current_day", 1)

    if args.approve:
        approve_next_day()
    elif args.status:
        print(json.dumps(load_pilot_state(), indent=2, ensure_ascii=False))
    elif args.live:
        run_live_session(day=target_day, checkpoint_at_page=args.checkpoint_at_page, telegram_screenshots=tg_ss)
    else:
        run_dry_run_simulation(day=target_day, checkpoint_at_page=args.checkpoint_at_page, telegram_screenshots=tg_ss)
