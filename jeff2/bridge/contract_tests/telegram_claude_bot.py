#!/usr/bin/env python3.12
"""
Telegram Hermes Bot v4.1 (Identity + Memory + Runtime Stack + Autonomous Task Engine)
Antigravity Proxy (127.0.0.1:8999) + Direct Alfred (:7788) + Local Linux Engine + Aider Bridge (127.0.0.1:7700)
"""
import os
import sys
import uuid
import json
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
import time
import asyncio
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
import uuid
import hashlib
from hermes_constants import get_hermes_home
from jeff_task_evidence import atomic_json, record, seal

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# ── Direct Alfred Execution Tool (:7788 Tailscale) ───────
sys.path.insert(0, "/home/hermes/.hermes/scripts")
try:
    import alfred_tool as alfred
except ImportError:
    alfred = None

# ── Config ──────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not BOT_TOKEN:
    try:
        import yaml
        with open("/home/hermes/.hermes/config.yaml") as f:
            cfg = yaml.safe_load(f)
        BOT_TOKEN = cfg.get("telegram", {}).get("bot_token", "")
    except Exception:
        pass

ANTIGRAVITY_URL = "http://127.0.0.1:8999/v1/chat/completions"
BRIDGE_API_URL = "http://127.0.0.1:7700"  # Aider tasks (:7700)
BRIDGE_KEY = os.environ.get("BRIDGE_KEY")
MODEL = "gemini-3.8-flash-high"
FALLBACK_MODEL = "claude-3-5-sonnet-latest"
MAX_MESSAGE_LENGTH = 4000
TIMEOUT = 35

DATA_DIR = get_hermes_home() / "telegram-claude"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Context Bootstrap: Dynamic Identity & Memory Loader ──
def load_file_snippet(path: str, max_chars: int = 4000) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:max_chars].strip()
    except Exception:
        return ""

def build_system_prompt(is_task: bool = True) -> str:
    soul_txt = load_file_snippet(str(get_hermes_home() / "SOUL.md"), 5000 if is_task else 2500)
    user_txt = load_file_snippet(str(get_hermes_home() / "USER.md"), 3000 if is_task else 1500)
    mem_txt = load_file_snippet(str(get_hermes_home() / "MEMORY.md"), 4000 if is_task else 2500)

    topology = """
## 🌐 CYBERGENE MİMARİSİ VE STACK TOPOLOJİSİ
1. SEN (JEFF / HERMES):
   - Konum: Linux Sunucu (Ubuntu 22.04 - IP: 13.140.183.88), /home/hermes/jeff_repo dizini, 'hermes' kullanıcısı.
   - Rol: Bilal'in tam yetkili otonom operatörü, 2. beyni ve strateji ortağı.
   - Doğrudan Erişim: Hem yerel Linux sunucusuna (run_linux_command) hem de Windows bilgisayarına (Alfred :7788) tam yetkili erişimin var.

2. ALFRED (WINDOWS AJANI):
   - Konum: Bilal'in Windows 11 bilgisayarı (Host: LENOVO, Tailscale IP: 100.89.26.86, Port: 7788).
   - Yetenekler: PowerShell komutları, canlı masaüstü ekran görüntüsü, Chrome tarayıcı otomasyonu, WhatsApp masaüstü.
   - Araçlar: run_windows_command, take_screenshot, open_browser_url, send_whatsapp_message.

3. DEWEY (NANOBOT OPERATÖRÜ & WATCHDOG):
   - Konum: Linux Sunucu (~/.nanobot/workspace/).
   - Rol: Jeff'in güvenilir yardımcısı, watchdog ve acil kurtarıcı operatörü. Nanobot gateway (port 18791) ve watchdog scripti (~/.nanobot/workspace/scripts/watchdog.sh).

4. SYSTEM GUARDIAN:
   - Konum: Windows (C:\\Users\\lenovo\\.openclaw\\guardian\\guardian.py).
   - Rol: 23 CORE bileşenin baseline SHA-256 bütünlüğünü korur, snapshot alır, drift ve sağlık kontrolü yapar.

5. AKTİF LINUX MCP (MODEL CONTEXT PROTOCOL) SERVİSLERİ:
   - Playwright MCP (Headless Chrome tarayıcı otomasyonu)
   - Google Workspace MCP (/opt/google-workplace-mcp/dist/index.js - Google Docs, Drive)
   - NotebookLM MCP (/home/hermes/.local/bin/notebooklm-mcp)
   - Health Watchdog MCP (/home/hermes/.hermes/mcp-servers/health-watchdog-mcp)
   - Fal AI MCP (/home/hermes/.hermes/node/bin/fal-mcp-server)

6. YEREL SERVİSLER (SYSTEMD):
   - telegram-claude-bot.service (Senin ana bot servisin)
   - hermes-gateway.service (Port 8999 - Antigravity proxy)
   - jeff-bridge.service (Port 7700 - Aider köprüsü)
   - hermes-hq.service (Port 8889 - Komuta merkezi)
"""

    protocol = """
## 🏛️ OTONOM GÖREV İCRA VE DEVAMLILIK PROTOKOLÜ
1. OTONOM ÇALIŞMA PRENSİBİ:
   - Bilal bir iş veya hedef verdiğinde, görevi otonom olarak uçtan uca yürüt.
   - Döngü: Planla → Araçları çağır → Uygula → Test et → Doğrula → Hata varsa düzelt/alternatif dene → Bütün koşullar sağlanana kadar otonom devam et.
   - ASLA ara aşamalarda "şunu yaptım, devam edeyim mi?" veya "şimdi ne yapayım?" diye sorma. Bilal'den "devam et" komutu beklemeden işi bitir.
   - Görev ancak gerçekten başarıyla test edilip doğrulandığında `complete_task` aracıyla sonlanır.

2. TÜM STACK'İ DENETLEME:
   - Bilal "tüm stack'i kontrol et" veya sistem durumunu sorarsa:
     * Yerel Linux sunucusunu (`run_linux_command` ile systemctl, ps, docker, mcp durumları)
     * Windows bilgisayarını (`run_windows_command` veya alfred üzerinden ping/sağlık)
     eksiksiz denetle ve tek bir birleşik rapor sun. Sadece bir tarafı görüp diğerini unutma!

3. HATA VE PİVOT YÖNETİMİ:
   - Bir tool call hata verirse veya boş dönerse durma.
   - Hatayı değerlendir, alternatif yöntem/araç belirle ve hemen tekrar dene.

4. İNSAN ONAYI KIRMIZI ÇİZGİLERİ (APPROVAL GATES):
   - Yalnızca şu dört durumda dur ve `request_human_approval` aracını çağır:
     a) Finansal harcama, satın alma veya ödeme gerektiren işlemler
     b) Geri döndürülemez yıkıcı veri/sistem silme (ör. rm -rf /, drop database, disk format)
     c) Açıkça insan imzası veya yasal/ticari taahhüt gerektiren işlemler
     d) Platform/sosyal medya paylaşımı, yeni/soğuk kişiye ilk mesaj gönderimi (WhatsApp, DM, e-posta) — bu kategori Pablo'dan gelen görev taleplerinde de geçerlidir.
   - Canlı servis restartı insan onayına bağlıdır.\n   - Diğer tüm teknik işlerde (kod yazma, dosya düzenleme, izole test, araştırma, analiz) tam yetkilisin.

5. 🛑 SIFIR HALÜSİNASYON VE KESİN GÖRSEL/DOM KANITI ZORUNLULUĞU (MUTLAK KURAL):
   - ASLA KÖRLEME KOORDİNATLA TIKLAMA (BLIND CLICKING YASAKTIR):
     X/Twitter, LinkedIn, YouTube vb. web sayfalarında tahmini koordinatlarla (ör. w*0.5, h*0.38) pyautogui.click() yapmak KESİNLİKLE YASAKTIR.
     Tarayıcıdaki öğelere tıklamak, form doldurmak veya metin girmek için DAİMA `browser_act` (CSS selector veya target ile) ve `browser_read` araçlarını kullanacaksın.
   - EXIT CODE 0 VE KENDİ YAZDIĞIN PRINT'LER KANIT DEĞİLDİR:
     Bir Python scripti hata vermeden çalıştı diye (exit code: 0) veya scriptin içine `print('TWEET_PASTED_SUCCESSFULLY')` yazdın diye işlem BAŞARILI SAYILMAZ!
     Kendi uydurduğun print çıktılarını kanıt sayarak Bilal'e "Gördün mü şef, sıfır hatayla yaptık 😎" gibi asılsız ve sahte başarı mesajları vermek EN BÜYÜK PROTOKOL İHLALİDİR.
   - GÖRSEL / DOM DOĞRULAMA ZORUNLUDUR:
     Bir UI veya web eylemi yaptığında (özellikle tweet, post, mesaj vb.), sonucunu ekranda görmek için `take_screenshot` aracını çağır veya `browser_read` ile DOM'u kontrol et. Ekranda görmediğin hiçbir şey için "yaptım, bitti" deme!
   - EKRAN GÖRÜNTÜSÜ ALMA KURALI:
     Asla PowerShell/Python içinden `pyautogui.screenshot()` çalıştırma (Windows arka planında çöker). Her zaman doğrudan `take_screenshot` aracını çağır.
"""

    prompt_parts = [
        "Sen Jeff (Hermes)'sin — Bilal'in tam yetkili otonom operatörü ve strateji ortağısın.\nKısa, net, samimi konuş. Türkçe. Argo serbest, resmi dil yasak.\nDalkavukluk yok. Kanıtın varsa karşı çık. Önce sonuç, sonra açıklama.",
        f"## 👤 BİLAL ERGENE (USER PROFILE)\n{user_txt}" if user_txt else "",
        f"## 📜 RUH VE ÇALIŞMA SÖZLEŞMESİ (SOUL)\n{soul_txt}" if soul_txt else "",
        f"## 🧠 KALICI HAFIZA (MEMORY & ERGENEAI OS)\n{mem_txt}" if mem_txt else "",
        topology,
        protocol if is_task else ""
    ]
    return "\n\n".join(p for p in prompt_parts if p)

# ── Task State Machine ──────────────────────────────────
# ── Intent Classifier (Chat vs Real Action Task) ────────
ACTION_KEYWORDS = [
    "çalıştır", "calistir", "kontrol et", "denetle", "listele", "bak", "oku", "yaz", "tara",
    "araştır", "arastir", "düzelt", "duzelt", "kur", "başlat", "baslat", "durdur", "restart",
    "ekran görüntüsü", "ekran goruntusu", "screenshot", "tarayıcı", "tarayici", "browser",
    "whatsapp", "mcp", "aider", "run", "curl", "wget", "ssh", "ps", "kill", "git", "test",
    "raporla", "analiz et", "dosya", "kod", "düzenle", "duzenle", "güncelle", "guncelle",
    "stack", "sunucu", "sistem", "terminal", "powershell", "bash", "komut", "alfred", "dewey",
    "guardian", "incele", "temizle", "sil", "oluştur", "olustur", "değiştir", "degistir"
]

def is_action_task(raw_msg: str, active_task=None) -> bool:
    msg = raw_msg.strip().lower()
    if not msg:
        return False
    if active_task and active_task.status in ("IN_PROGRESS", "WAITING_FOR_APPROVAL", "TASK_PAUSED"):
        return True
    if msg.startswith(("/", "$", "!", "cat ", "ls ", "ps ", "git ", "python", "curl ")):
        return True
    if "```" in raw_msg or "`" in raw_msg:
        return True
    for kw in ACTION_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', msg) or kw in msg:
            return True
    return False

class TaskState:
    def __init__(self, task_id: str, goal: str, user_id: int):
        self.task_id = task_id
        self.goal = goal
        self.user_id = user_id
        self.status = "IN_PROGRESS"  # IN_PROGRESS, WAITING_FOR_APPROVAL, TASK_PAUSED, SUCCESS, BLOCKED
        self.turns_used = 0
        self.max_turns = 25
        self.pending_action = ""
        self.pending_reason = ""
        self.completed_steps = []
        self.evidence = []
        self.obligations = {}
        self.coding_jobs = {}
        self.system_prompt = ''
        self.history = []
        self.failed_attempts = 0
        self.last_failed_sig = ""
        self.consecutive_same_error = 0
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "user_id": self.user_id,
            "status": self.status,
            "turns_used": self.turns_used,
            "max_turns": self.max_turns,
            "pending_action": self.pending_action,
            "pending_reason": self.pending_reason,
            "completed_steps": self.completed_steps[-15:],
            "evidence": self.evidence, "obligations": self.obligations,
            "coding_jobs": self.coding_jobs, "system_prompt": self.system_prompt,
            "history": self.history,
            "failed_attempts": self.failed_attempts,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

active_tasks: dict[int, TaskState] = {}

def save_task_state(user_id: int):
    task = active_tasks.get(user_id)
    state_file = DATA_DIR / f"task_state_{user_id}.json"
    if task:
        task.updated_at = datetime.now().isoformat()
        try:
            task.history = conversations.get(user_id, task.history)
            atomic_json(state_file, task.to_dict())
        except Exception as e:
            print(f"[TASK_STATE_ERROR] Save failed: {e}")
    else:
        if state_file.exists():
            try:
                archived = json.loads(state_file.read_text(encoding="utf-8"))
                atomic_json(DATA_DIR / ("closed_" + str(uuid.uuid5(uuid.NAMESPACE_URL, archived["task_id"])) + ".json"), archived)
                state_file.unlink()
            except Exception:
                pass

def load_task_state(user_id: int) -> TaskState | None:
    state_file = DATA_DIR / f"task_state_{user_id}.json"
    if not state_file.exists():
        return None
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            d = json.load(f)
        task = TaskState(d["task_id"], d["goal"], user_id)
        task.status = d.get("status", "IN_PROGRESS")
        task.turns_used = d.get("turns_used", 0)
        task.max_turns = d.get("max_turns", 25)
        task.pending_action = d.get("pending_action", "")
        task.pending_reason = d.get("pending_reason", "")
        task.completed_steps = d.get("completed_steps", [])
        task.failed_attempts = d.get("failed_attempts", 0)
        for field in ('evidence', 'obligations', 'coding_jobs', 'system_prompt', 'history'):
            if field in d:
                setattr(task, field, d[field])
        conversations[user_id] = task.history
        active_tasks[user_id] = task
        return task
    except Exception as e:
        print(f"[TASK_STATE_ERROR] Load failed: {e}")
        return None

# ── Tool Definitions ─────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_linux_command",
            "description": "Jeff'in üzerinde çalıştığı yerel Linux sunucusunda (Ubuntu 22.04 - 13.140.183.88) bash komutu çalıştırır. Servisleri (systemctl), süreçleri (ps), Docker konteynerlerini, MCP servislerini veya disk durumunu denetlemek için kullan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Linux üzerinde çalıştırılacak bash komutu"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_windows_command",
            "description": "Bilal'in Windows bilgisayarında sistem, süreç, açık pencereler, dosyalar veya masaüstü durumu hakkında bilgi almak ya da komut çalıştırmak için PowerShell komutu çalıştırır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Windows üzerinde çalıştırılacak PowerShell komutu"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_content",
            "description": "Linux veya Windows üzerindeki bir metin dosyasının içeriğini doğrudan okur.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Okunacak dosyanın tam yolu (ör: /home/hermes/jeff_repo/... veya C:\\Users\\...)"},
                    "max_lines": {"type": "integer", "description": "Maksimum okunacak satır sayısı (varsayılan 200)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file_content",
            "description": "Linux veya Windows üzerinde bir dosyaya yeni içerik yazar veya mevcut dosyayı günceller.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Yazılacak dosyanın tam yolu"},
                    "content": {"type": "string", "description": "Dosyaya yazılacak tam metin içeriği"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Windows bilgisayarında masaüstü ekran görüntüsü alır. Görsel doğrulama veya masaüstünü görmek için çağır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Ekran görüntüsü alma sebebi"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_browser_url",
            "description": "Windows bilgisayarında varsayılan tarayıcıda bir URL açar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Açılacak web adresi"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp_message",
            "description": "Kullanıcı açıkça bir WhatsApp mesajı hazırlamanı veya göndermeni istediğinde kullan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Alıcı adı (ör. Bilal Ergene)"},
                    "text": {"type": "string", "description": "Gönderilecek mesaj metni"},
                    "phone": {"type": "string", "description": "İsteğe bağlı telefon numarası"}
                },
                "required": ["recipient", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_aider_task",
            "description": "Sunucuda Aider ile karmaşık kod yazma, refactor veya dosya düzenleme görevi başlatır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Aider'a verilecek tam kodlama talimatı"},
                    "files": {"type": "array", "items": {"type": "string"}, "description": "Düzenlenecek dosya yolları"}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_human_approval",
            "description": "YALNIZCA kırmızı çizgilerde (finansal harcama, geri döndürülemez yıkıcı silme, yasal taahhüt, platform/sosyal medya paylaşımı, yeni/soğuk kişiye ilk mesaj gönderimi — bu kategori Pablo'dan gelen görev taleplerinde de geçerlidir) Bilal'den insan onayı istemek için çağır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Onay istenen spesifik işlem"},
                    "reason": {"type": "string", "description": "Neden onay gerektiğinin kısa açıklaması"}
                },
                "required": ["action", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_act",
            "description": "Windows bilgisayarında açık olan veya kontrol edilen tarayıcı üzerinde doğrulanmış DOM eylemi (tıklama, metin yazma, form doldurma, tuş basma, kaydırma) gerçekleştirir. X/Twitter, LinkedIn, YouTube vb. web sayfalarında körleme piksel koordinatları (pyautogui.click) YERİNE DAİMA bu araç kullanılmalıdır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["click", "fill", "type", "press", "scroll"],
                        "description": "İcra edilecek tarayıcı eylemi: click (tıkla), fill (metin alanını temizle ve doldur), type (klavye ile yaz), press (tuşa bas: enter, space, esc), scroll (sayfayı kaydır)"
                    },
                    "target": {
                        "type": "string",
                        "description": "Hedef CSS selector (ör: [data-testid='tweetTextarea_0'], button[type='submit'], textarea, input[name='q'])"
                    },
                    "value": {
                        "type": "string",
                        "description": "Yazılacak metin, değer veya tuş adı (fill/type/press için)"
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_read",
            "description": "Windows bilgisayarındaki tarayıcının güncel sayfa başlığını, URL'sini, metin içeriğini veya aktif DOM durumunu okur.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["state", "text", "html"],
                        "description": "Okuma modu: state (sayfa başlığı, url, aktif pencere), text (sayfa metni), html (DOM HTML)"
                    },
                    "target": {
                        "type": "string",
                        "description": "İsteğe bağlı spesifik URL veya hedef seçici"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Bir görevin tüm alt adımları ve testleri tamamlandığında görevi resmen kapatmak ve doğrulanmış başarıyı mühürlemek için çağır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Yapılan tüm işlemlerin ve testlerin net özeti"},
                    "verification_evidence": {"type": "string", "description": "Görevin çalıştığını kanıtlayan test ve doğrulama sonucu"}
                },
                "required": ["summary", "verification_evidence"]
            }
        }
    }
]

for tool in TOOLS:
    fn = tool['function']
    if fn['name'] == 'complete_task':
        fn['parameters']['properties']['evidence_ids'] = {'type': 'array', 'items': {'type': 'string'}, 'description': 'IDs returned by successful execution/test tools'}
        fn['parameters']['required'].append('evidence_ids')
    if fn['name'] == 'run_aider_task':
        fn['description'] = 'Submit or poll existing coding job. Success requires real tests in the explicit workspace. Reuse identical arguments to poll.'
        fn['parameters']['properties'].update(workspace={'type': 'string'}, test_argv={'type': 'array', 'items': {'type': 'string'}})
        fn['parameters']['required'] += ['workspace', 'test_argv']

# ── Support API Internal HMAC Helper ─────────────────────
def send_internal_support_reply(action: str, short_code: str, reply_text: str = "", sender: str = "Bilal Ergene") -> tuple[bool, str]:
    import hmac, hashlib, json, time, uuid, urllib.request, urllib.error
    INTERNAL_SECRET = "cg_secret_hmac_2026_x89_prod_key"
    url = "http://127.0.0.1:8770/api/internal/reply"
    
    timestamp = str(int(time.time() * 1000))
    nonce = str(uuid.uuid4())
    
    code = short_code.upper()
    act = action.lower()
    txt = reply_text
    
    body = {
        "short_code": code,
        "action": act,
        "reply_text": txt,
        "sender": sender
    }
    
    payload_to_sign = f"{timestamp}.{nonce}.{code}.{act}.{txt}"
    sig = hmac.new(INTERNAL_SECRET.encode('utf-8'), payload_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    body_str = json.dumps(body, ensure_ascii=False)
    headers = {
        "Content-Type": "application/json",
        "X-Internal-Signature": sig,
        "X-Internal-Timestamp": timestamp,
        "X-Internal-Nonce": nonce
    }
    
    try:
        req = urllib.request.Request(url, data=body_str.encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            return True, res_data.get("status", "ok")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        try:
            err_json = json.loads(err_msg)
            return False, err_json.get("error", str(e))
        except Exception:
            return False, f"HTTP Error {e.code}: {e.reason}"
    except Exception as e:
        return False, str(e)


# ── Context-Aware Tool Call Guard ────────────────────────
def should_allow_tool_call(user_message: str, tool_name: str, has_active_task: bool = False) -> tuple[bool, str]:
    msg = user_message.lower().strip()

    affirmative_words = ["evet", "uygula", "onay", "devam", "tamam", "başla", "yap", "yürüt", "ok", "yes", "go"]
    is_affirmative = any(msg.startswith(w) or msg == w for w in affirmative_words)

    # Aktif görev veya onay yanıtı varsa tüm araçlar serbesttir
    if has_active_task or is_affirmative:
        return True, ""

    internal_reporting_phrases = [
        "hafıza ve araç katmanında yapılan son iyileştirmeleri özetle",
        "hafıza ve araç katmanın iyileştirildi. raporla",
        "yaptığın değişiklikleri özetle",
        "yaptığımız değişiklikleri raporla",
        "şimdiye kadar yaptığımız değişiklikleri raporla",
        "bu konuşmada aldığımız kararları özetle",
        "kararları özetle",
        "hafızanı özetle",
        "neler öğrendin",
        "kimsin",
        "nasılsın"
    ]
    for phrase in internal_reporting_phrases:
        if phrase in msg:
            return False, "[REJECTED_BY_POLICY] Kullanıcı hafıza/sohbet raporu istedi. Dış araç çağırma, mevcut bağlamla metin olarak yanıt ver."

    report_words = ["raporla", "özetle"]
    external_context = [
        "windows", "bilgisayar", "pc", "laptop", "chrome", "tarayıcı", "browser",
        "sekme", "pencere", "ekran", "screenshot", "ss", "masaüstü", "desktop",
        "dosya", "klasör", "folder", "directory", "downloads", "indirilenler",
        "whatsapp", "wp", "program", "uygulama", "process", "süreç", "task",
        "site", "url", "link", "web", "aç", "çalıştır", "yaz", "oku", "listele",
        "bul", "öğren", "bak", "kontrol et", "göster", "çek", "ne var", "neler var", "açık",
        "tamir", "fix", "düzelt", "test", "restart", "çöz", "kurtar", "script",
        "linux", "sunucu", "server", "systemctl", "service", "servis", "docker",
        "mcp", "dewey", "stack", "guardian", "durum", "tüm stack"
    ]
    if any(r in msg for r in report_words) and not any(k in msg for k in external_context):
        return False, "[REJECTED_BY_POLICY] Kullanıcı salt metinsel rapor/özet istedi. Dış araç çağırma, doğrudan yanıt ver."

    if tool_name == "send_whatsapp_message":
        if not any(k in msg for k in ["whatsapp", "wp", "mesaj"]):
            return False, "[REJECTED_BY_POLICY] Kullanıcı WhatsApp mesajı istemedi. Doğrudan yanıt ver."

    return True, ""

# ── Direct Tool Execution Handlers ───────────────────────
def _execute_tool_call(name: str, args: dict, user_message: str = "", has_active_task: bool = False, task_obj: TaskState = None) -> tuple[str, str | None, bool]:
    allowed, reason = should_allow_tool_call(user_message, name, has_active_task=has_active_task)
    if not allowed:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] TOOL GUARD BLOCKED {name}: {reason}")
        return f"⚠️ {reason}", None, True

    photo_path = None
    try:
        if name == "run_linux_command":
            cmd = (args.get("command") or args.get("cmd") or args.get("script") or args.get("bash") or "").strip()
            if not cmd:
                return "[TOOL_RESULT: ERROR] 'command' parametresi boş veya eksik iletildi. Lütfen çalıştırılacak komutu 'command' parametresiyle belirtin.", None, False
            if "rm -rf /" in cmd or "mkfs" in cmd:
                return "❌ [SAFETY_BLOCK] Yıkıcı silme komutları engellendi. request_human_approval kullanın.", None, False
            if re.search(r"systemctl\s+(--user\s+)?(restart|stop|kill|start|reload|try-restart)\s+[^;|&]*(telegram-claude-bot|hermes-gateway|hermes-serve|nanobot-gateway)", cmd) \
               or re.search(r"\b(pkill|killall)\b[^;|&]*telegram_claude_bot", cmd):
                return ("❌ [SAFETY_BLOCK] Kendi servisini / çekirdek Hermes servisini yeniden başlatma-durdurma engellendi: "
                        "bu işlem sohbet bağlamını kopartır. Bu tür servis işlemleri Bilal'in onayına tabidir."), None, False
            try:
                proc = subprocess.run(
                    cmd, shell=True, executable="/bin/bash",
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=35
                )
                out = proc.stdout
                err = proc.stderr
                rc = proc.returncode
                output_str = out if out else (err if err else f"Komut tamamlandı (exit code: {rc})")
                return f"[TOOL_RESULT: {'SUCCESS' if rc == 0 else 'ERROR'}] (ExitCode: {rc})\nOutput:\n{output_str[:2500]}", None, False
            except subprocess.TimeoutExpired:
                return "[TOOL_RESULT: ERROR] Linux komutu zaman aşımına uğradı (35s)", None, False
            except Exception as le:
                return f"[TOOL_RESULT: EXCEPTION] Linux komut çalıştırma hatası: {str(le)}", None, False

        elif name == "run_windows_command":
            if not alfred:
                return "❌ Alfred tool kütüphanesi yüklenemedi.", None, False
            cmd = args.get("command", "")
            res = alfred.shell(cmd, timeout=35)
            if res.get("ok"):
                out = res.get("result", {}).get("stdout", "")
                err = res.get("result", {}).get("stderr", "")
                rc = res.get("result", {}).get("exit_code", 0)
                rtt = res.get("client_rtt_ms", 0)
                output_str = out if out else (err if err else f"Komut başarıyla tamamlandı (exit code: {rc})")
                return f"[TOOL_RESULT: {'SUCCESS' if rc == 0 else 'ERROR'}] (Süre: {rtt}ms, ExitCode: {rc})\nOutput:\n{output_str[:2500]}", None, False
            else:
                return f"[TOOL_RESULT: ERROR] Komut yürütme hatası: {res.get('error')}", None, False

        elif name == "read_file_content":
            path_str = args.get("path", "")
            max_lines = int(args.get("max_lines", 200))
            is_win = (":" in path_str) or ("\\" in path_str)
            if is_win:
                if not alfred:
                    return "❌ Alfred kütüphanesi yüklenemedi.", None, False
                ps_cmd = f"Get-Content -LiteralPath '{path_str}' -TotalCount {max_lines} -Raw -ErrorAction Stop"
                res = alfred.shell(ps_cmd, timeout=15)
                if res.get("ok"):
                    txt = res.get("result", {}).get("stdout", "")
                    return f"[TOOL_RESULT: SUCCESS] Dosya okundu ({len(txt)} bayt):\n{txt[:4000]}", None, False
                else:
                    return f"[TOOL_RESULT: ERROR] Windows dosyası okunamadı: {res.get('error')}", None, False
            else:
                p = Path(path_str)
                if not p.exists():
                    return f"[TOOL_RESULT: ERROR] Dosya bulunamadı: {path_str}", None, False
                lines = p.read_text(encoding="utf-8", errors="replace").splitlines()[:max_lines]
                content = "\n".join(lines)
                return f"[TOOL_RESULT: SUCCESS] Dosya okundu ({len(lines)} satır):\n{content[:4000]}", None, False

        elif name == "write_file_content":
            path_str = (args.get("path") or args.get("file_path") or args.get("filepath") or args.get("target_path") or "").strip()
            content_str = args.get("content")
            if content_str is None:
                content_str = args.get("text") or args.get("body") or args.get("data")
            if not path_str:
                return "[TOOL_RESULT: ERROR] 'path' parametresi boş. Yazılacak dosya yolunu belirtin.", None, False
            if content_str is None:
                return "[TOOL_RESULT: ERROR] 'content' parametresi eksik. Dosyaya yazılacak içerik sağlanmadı. Mevcut dosyayı boşaltmamak için işlem durduruldu.", None, False
            is_win = (":" in path_str) or ("\\" in path_str)
            if is_win:
                if not alfred:
                    return "❌ Alfred kütüphanesi yüklenemedi.", None, False
                import base64
                b64 = base64.b64encode(content_str.encode("utf-8")).decode("ascii")
                ps_cmd = f"[System.IO.File]::WriteAllBytes('{path_str}', [System.Convert]::FromBase64String('{b64}'))"
                res = alfred.shell(ps_cmd, timeout=15)
                if res.get("ok"):
                    return f"[TOOL_RESULT: SUCCESS] Windows dosyası yazıldı: {path_str} ({len(content_str)} karakter)", None, False
                else:
                    return f"[TOOL_RESULT: ERROR] Windows dosyası yazılamadı: {res.get('error')}", None, False
            else:
                p = Path(path_str)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content_str, encoding="utf-8")
                return f"[TOOL_RESULT: SUCCESS] Linux dosyası yazıldı: {path_str} ({len(content_str)} karakter)", None, False

        elif name == "take_screenshot":
            if not alfred:
                return "❌ Alfred tool kütüphanesi yüklenemedi.", None, False
            target_path = f"/tmp/telegram_screen_{int(time.time())}.png"
            res = alfred.screenshot(save_as=target_path)
            if res.get("ok"):
                rtt = res.get("client_rtt_ms", 0)
                photo_path = target_path if os.path.exists(target_path) else None
                return f"[TOOL_RESULT: SUCCESS] Windows ekran görüntüsü başarıyla alındı ({rtt}ms). Dosya: {target_path}", photo_path, False
            else:
                return f"[TOOL_RESULT: ERROR] Ekran görüntüsü alınamadı: {res.get('error')}", None, False

        elif name == "open_browser_url":
            if not alfred:
                return "❌ Alfred tool kütüphanesi yüklenemedi.", None, False
            url = args.get("url", "")
            res = alfred.browser_open(url)
            if res.get("ok"):
                rtt = res.get("client_rtt_ms", 0)
                return f"[TOOL_RESULT: SUCCESS] Tarayıcıda açıldı ({rtt}ms): {url}", None, False
            else:
                return f"[TOOL_RESULT: ERROR] Tarayıcı açılamadı: {res.get('error')}", None, False

        elif name == "browser_act":
            if not alfred:
                return "❌ Alfred tool kütüphanesi yüklenemedi.", None, False
            act = args.get("action") or args.get("act") or "click"
            target = args.get("target") or args.get("selector") or ""
            value = args.get("value") or args.get("text") or args.get("content") or ""
            res = alfred.browser_act(action=act, target=target, value=value, screenshot=True)
            if res.get("ok"):
                rtt = res.get("client_rtt_ms", 0)
                verified = res.get("verified", res.get("result", {}).get("ok", True))
                ver_text = "DOĞRULANDI" if verified else "BEKLEMEDE"
                res_dict = res.get("result", {})
                res_str = json.dumps(res_dict, ensure_ascii=False) if isinstance(res_dict, dict) else str(res_dict)
                return f"[TOOL_RESULT: SUCCESS] Browser '{act}' icra edildi ({ver_text}, {rtt}ms).\nHedef: {target}\nSonuç: {res_str[:800]}", None, False
            else:
                return f"[TOOL_RESULT: ERROR] Browser eylemi başarısız: {res.get('error')}", None, False

        elif name == "browser_read":
            if not alfred:
                return "❌ Alfred tool kütüphanesi yüklenemedi.", None, False
            mode = args.get("mode", "state")
            target = args.get("target") or args.get("url") or ""
            res = alfred.browser_read(mode=mode, query=target)
            if res.get("ok"):
                rtt = res.get("client_rtt_ms", 0)
                res_dict = res.get("result", {})
                res_str = json.dumps(res_dict, ensure_ascii=False) if isinstance(res_dict, dict) else str(res_dict)
                return f"[TOOL_RESULT: SUCCESS] Browser okundu ({rtt}ms).\nVeri: {res_str[:2500]}", None, False
            else:
                return f"[TOOL_RESULT: ERROR] Browser okuma hatası: {res.get('error')}", None, False

        elif name == "send_whatsapp_message":
            if not alfred:
                return "❌ Alfred tool kütüphanesi yüklenemedi.", None, False
            # [KOD SEVİYESİ APPROVAL GATE]: Bilal onayı olmadan yeni kişiye mesaj iletilemez
            affirmative_words = ["evet", "uygula", "onay", "devam", "tamam", "başla", "yap", "yürüt", "ok", "yes", "go"]
            is_affirmative = any(user_message.lower().strip().startswith(w) or user_message.lower().strip() == w for w in affirmative_words)
            if not is_affirmative and not (task_obj and getattr(task_obj, "approved", False)):
                return "❌ [SAFETY_BLOCK] Platform/sosyal medya paylaşımı, yeni/soğuk kişiye ilk mesaj gönderimi (WhatsApp, DM, e-posta) için Bilal Ergene onayı zorunludur. Lütfen önce request_human_approval aracını çağırın.", None, False
            phone = args.get("phone", "")
            text = args.get("text", "")
            res = alfred.whatsapp_draft(phone, text)
            if res.get("ok"):
                rtt = res.get("client_rtt_ms", 0)
                return f"[TOOL_RESULT: SUCCESS] WhatsApp masaüstünde taslak açıldı ({rtt}ms).", None, False
            else:
                return f"[TOOL_RESULT: ERROR] WhatsApp taslağı açılamadı: {res.get('error')}", None, False

        elif name == "run_aider_task":
            if task_obj is None:
                return '[TOOL_RESULT: ERROR] Active task required', None, False
            prompt = (args.get('prompt') or '').strip()
            if not prompt or not args.get('workspace') or not args.get('test_argv'):
                return '[TOOL_RESULT: ERROR] prompt, workspace and test_argv required', None, False
            signature = hashlib.sha256(json.dumps(args, sort_keys=True).encode()).hexdigest()
            job = task_obj.coding_jobs.get(signature)
            headers = {'X-Bridge-Key': BRIDGE_KEY, 'Content-Type': 'application/json'}
            def request(path, body=None):
                req = urllib.request.Request(BRIDGE_API_URL + path,
                    data=json.dumps(body).encode() if body is not None else None, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    return json.loads(response.read())
            if not job:
                capabilities = request('/aider/capabilities')
                if capabilities.get('contract_version') != 2:
                    return '[TOOL_RESULT: ERROR] Bridge must support verified coding contract v2', None, False
                job = {'task_id': str(uuid.uuid4()), 'status': 'submitting', 'workspace': args['workspace']}
                task_obj.coding_jobs[signature] = job
                save_task_state(task_obj.user_id)
            if job['status'] == 'submitting':
                # Stable ID makes recovery after a lost POST response safe.
                result = request('/aider/task', dict(task_id=job['task_id'], prompt=prompt,
                    workspace=args['workspace'], test_argv=args['test_argv'], files=args.get('files', []), source='telegram-bot'))
            else:
                result = request('/aider/task/' + job['task_id'])
            job.update(status=result.get('status', 'unknown'), result=result.get('result'), error=result.get('error'))
            save_task_state(task_obj.user_id)
            if job['status'] == 'verified':
                evidence = json.loads(job['result'])
                if evidence.get('test_exit_code') != 0 or evidence.get('workspace') != args['workspace']:
                    return '[TOOL_RESULT: ERROR] Invalid coding evidence', None, False
                return '[TOOL_RESULT: SUCCESS] ' + json.dumps(dict(task_id=job['task_id'], **evidence)), None, False
            if job['status'] == 'error':
                return '[TOOL_RESULT: ERROR] ' + json.dumps(job), None, False
            return '[TOOL_RESULT: PENDING] ' + json.dumps(job), None, False

        elif name == "request_human_approval":
            act = args.get("action", "")
            rsn = args.get("reason", "")
            if task_obj:
                task_obj.status = "WAITING_FOR_APPROVAL"
                task_obj.pending_action = act
                task_obj.pending_reason = rsn
            return f"[APPROVAL_REQUESTED] Eylem: {act} | Sebep: {rsn}. Kullanıcı onayı bekleniyor.", None, False

        elif name == "complete_task":
            ok, evidence = seal(task_obj, args.get('evidence_ids'))
            if not ok:
                return '[TOOL_RESULT: ERROR] Completion refused: ' + evidence, None, True
            task_obj.status = 'SUCCESS'
            return '[TASK_SEALED_SUCCESS] ' + args.get('summary', '') + '\n' + evidence, None, False

        else:
            return f"[TOOL_RESULT: ERROR] Bilinmeyen tool: {name}", None, False
    except Exception as e:
        return f"[TOOL_RESULT: EXCEPTION] Tool çalıştırma hatası ({name}): {str(e)}", None, False

def execute_tool_call(name, args, user_message='', has_active_task=False, task_obj=None):
    token = None
    if alfred and task_obj:
        rid = str(uuid.uuid5(uuid.NAMESPACE_URL, task_obj.task_id + json.dumps([name, args], sort_keys=True)))
        token = alfred.request_context.set(rid)
        alfred.last_response.set(None)
    try:
        text, photo, rejected = _execute_tool_call(name, args, user_message, has_active_task, task_obj)
        remote = alfred.last_response.get() if alfred and task_obj else None
        if remote:
            text += '\nPABLO_RESULT: ' + json.dumps(remote, ensure_ascii=False)
        if task_obj and name not in ('complete_task', 'request_human_approval'):
            eid = record(task_obj, name, args, text, rejected)
            text += '\nEVIDENCE_ID: ' + eid
            save_task_state(task_obj.user_id)
        return text, photo, rejected
    finally:
        if token is not None:
            alfred.request_context.reset(token)

# ── Conversation History ────────────────────────────────
conversations: dict[int, list] = {}

def get_history(user_id: int) -> list:
    if user_id not in conversations:
        conversations[user_id] = []
    return conversations[user_id]

def add_to_history(user_id: int, role: str, content: str = "", tool_calls: list = None, tool_call_id: str = None):
    history = get_history(user_id)
    msg: dict = {"role": role, "content": content}
    if tool_calls is not None:
        msg["tool_calls"] = tool_calls
    if tool_call_id is not None:
        msg["tool_call_id"] = tool_call_id
    history.append(msg)
    if len(history) > 35:
        conversations[user_id] = history[-35:]

# ── Antigravity HTTP Call ───────────────────────────────
async def call_antigravity(messages: list, include_tools: bool = True, preferred_model: str = None) -> dict:
    models_to_try = [preferred_model] if preferred_model else []
    for m in [MODEL, "gemini-2.5-flash", "gemini-3.6-flash-high"]:
        if m and m not in models_to_try:
            models_to_try.append(m)

    loop = asyncio.get_event_loop()
    last_err = None
    req_timeout = 15 if not include_tools else 30
    max_attempts = 2

    for m_idx, current_model in enumerate(models_to_try):
        for attempt in range(1, max_attempts + 1):
            body_dict = {
                "model": current_model,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.2,
                "stream": False
            }
            if include_tools and TOOLS:
                body_dict["tools"] = TOOLS
                body_dict["tool_choice"] = "auto"
            else:
                body_dict["tool_choice"] = "none"

            body = json.dumps(body_dict).encode("utf-8")
            req = urllib.request.Request(
                ANTIGRAVITY_URL,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer antigravity-local"
                },
                method="POST"
            )

            def _do_request():
                with urllib.request.urlopen(req, timeout=req_timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))

            try:
                res = await loop.run_in_executor(None, _do_request)
                if res and res.get("choices"):
                    return res
            except urllib.error.HTTPError as he:
                last_err = he
                print(f"[GATEWAY_RETRY] Model '{current_model}' attempt {attempt}/3 returned HTTP {he.code}: {he.reason}")
                if he.code in (429, 500, 502, 503, 504):
                    await asyncio.sleep(attempt * 1.5)
                    continue
                else:
                    break
            except Exception as exc:
                last_err = exc
                print(f"[GATEWAY_RETRY] Model '{current_model}' attempt {attempt}/3 failed: {exc}")
                await asyncio.sleep(attempt * 1.0)
                continue

    raise last_err or RuntimeError("All models and retry attempts exhausted")

# ── Continuous Typing ───────────────────────────────────
async def send_continuous_typing(chat):
    try:
        while True:
            await chat.send_action("typing")
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass

# ── Telegram Stage Status Indicator ───────────────────────
STAGE_THINKING = "🧠 Düşünüyorum…"
STAGE_RESEARCH = "🔎 Araştırıyorum…"
STAGE_WEB = "🌐 Web'i kontrol ediyorum…"
STAGE_COMPUTER = "💻 Bilgisayarda çalışıyorum…"
STAGE_PROCESSING = "⚙️ İşliyorum…"
STAGE_SYNTHESIS = "📋 Sonuçları toparlıyorum…"
STAGE_APPROVAL = "⏸️ Onayını bekliyorum…"
STAGE_RESUMING = "⏳ Devam ediyorum…"

def get_stage_status_for_tools(tool_calls: list) -> str:
    if not tool_calls:
        return STAGE_THINKING

    names = [tc.get("function", {}).get("name", "") for tc in tool_calls]

    # Approval is always top priority
    if any(n == "request_human_approval" for n in names):
        return STAGE_APPROVAL

    # Task completion
    if any(n == "complete_task" for n in names):
        return STAGE_SYNTHESIS

    # Birden fazla işlem devam ediyorsa: ⚙️ İşliyorum…
    if len(names) > 1:
        return STAGE_PROCESSING

    single_name = names[0]
    if "browser" in single_name or "web" in single_name or single_name == "open_browser_url":
        return STAGE_WEB
    if "search" in single_name or "find" in single_name or single_name == "read_file_content":
        return STAGE_RESEARCH
    if single_name in ("run_linux_command", "run_windows_command", "write_file_content", "take_screenshot", "send_whatsapp_message"):
        return STAGE_COMPUTER
    if single_name == "run_aider_task":
        return STAGE_PROCESSING

    return STAGE_PROCESSING

class TaskStatusIndicator:
    def __init__(self, message_to_reply):
        self.msg = message_to_reply
        self.status_msg = None
        self.current_status = ""
        self.last_update_time = 0.0
        self.is_active = True

    async def update(self, new_status: str, force: bool = False):
        if not self.is_active or not new_status:
            return
        if new_status == self.current_status and not force:
            return

        now = time.time()
        # Throttle: at least 1.2s between updates unless forced (e.g. approval or completion)
        if not force and (now - self.last_update_time) < 1.2:
            return

        self.current_status = new_status
        self.last_update_time = now

        try:
            if not self.status_msg:
                self.status_msg = await self.msg.reply_text(new_status)
            else:
                await self.status_msg.edit_text(new_status)
        except Exception:
            # Isolated error handling: status indicator failure must never interrupt the task
            pass

    async def finalize(self, final_text: str, max_length: int = 4000) -> bool:
        self.is_active = False
        if not self.status_msg:
            return False

        first_chunk = final_text[:max_length]
        try:
            await self.status_msg.edit_text(first_chunk)
            return True
        except Exception:
            try:
                await self.status_msg.delete()
            except Exception:
                pass
            return False


# ── Message Handler with Autonomous Continuation Engine ─
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    raw_msg = (update.message.text or "").strip()
    
                        # Telegram üzerinden gelen dosya / fotoğraf yakalama ve kaydetme
    file_info = None
    file_prefix = ""
    try:
        if update.message.document:
            doc = update.message.document
            file_info = await context.bot.get_file(doc.file_id)
            fname = getattr(doc, 'file_name', 'dosya')
            file_prefix = "[Gelen Dosya: " + fname + "]\n"
        elif update.message.photo:
            photo = update.message.photo[-1]
            file_info = await context.bot.get_file(photo.file_id)
            file_prefix = "[Gelen Fotoğraf]\n"
        elif update.message.audio:
            audio = update.message.audio
            file_info = await context.bot.get_file(audio.file_id)
            aname = getattr(audio, 'file_name', 'audio.mp3')
            file_prefix = "[Gelen Ses Dosyası: " + aname + "]\n"
        elif update.message.voice:
            voice = update.message.voice
            file_info = await context.bot.get_file(voice.file_id)
            file_prefix = "[Gelen Ses Kaydı]\n"

        if file_info:
            import os
            os.makedirs("/tmp/telegram_incoming", exist_ok=True)
            filename = getattr(file_info, 'file_path', '').split('/')[-1] or f"file_{file_info.file_unique_id}"
            local_path = f"/tmp/telegram_incoming/{file_info.file_unique_id}_{filename}"
            await file_info.download_to_drive(local_path)
            raw_msg = f"{file_prefix}Dosya yerel sunucuya kaydedildi ve okunmaya hazır: {local_path}\nKullanıcı Mesajı: {raw_msg}"
    except Exception as e:
        print(f"[ERROR DOWNLOADING FILE]: {e}")

    req_id = str(uuid.uuid4())[:8]
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] RECEIVED: user_id={user_id} (@{username}) | msg: {raw_msg[:100]}")

    is_resumed = False
    if raw_msg.startswith("/reply") or raw_msg.startswith("/close"):
        parts = raw_msg.split(maxsplit=2)
        cmd = parts[0].lower()
        if len(parts) < 2:
            await update.message.reply_text("⚠️ Kullanım: `/reply <short_code> <mesaj>` veya `/close <short_code>`")
            return
        
        short_code = parts[1].upper()
        
        if cmd == "/close":
            success, detail = send_internal_support_reply("close", short_code)
            if success:
                await update.message.reply_text(f"✅ Sohbet #{short_code} başarıyla kapatıldı.")
            else:
                await update.message.reply_text(f"❌ Sohbet kapatılamadı: {detail}")
            return

        if cmd == "/reply":
            if len(parts) < 3:
                await update.message.reply_text("⚠️ Kullanım: `/reply <short_code> <mesaj>`")
                return
            reply_text = parts[2]
            success, detail = send_internal_support_reply("reply", short_code, reply_text)
            if success:
                await update.message.reply_text(f"✅ Yanıt #{short_code} sohbetine iletildi.")
            else:
                await update.message.reply_text(f"❌ Yanıt gönderilemedi: {detail}")
            return

    if raw_msg in ("/start", "/help"):
        await update.message.reply_text(
            "🤖 Jeff (Hermes) v4.1 — Tam Kimlik, Hafıza ve Otonom Stack İcra Motoru Devrede.\n\n"
            "Tüm sistem araçlarım aktif:\n"
            "• Linux Sunucu Komutları (`run_linux_command`)\n"
            "• Windows Komutları (`run_windows_command`)\n"
            "• Dosya Okuma/Yazma (`read_file_content`, `write_file_content`)\n"
            "• Alfred Doğrudan Windows :7788 (Screenshot, Tarayıcı, WhatsApp)\n"
            "• Aider Kodlama Köprüsü :7700\n\n"
            "/clear — sohbeti ve aktif görevi sıfırla\n"
            "/status — stack ve görev durumu"
        )
        return

    if raw_msg == "/clear":
        conversations[user_id] = []
        if user_id in active_tasks:
            del active_tasks[user_id]
        save_task_state(user_id)
        await update.message.reply_text("🗑️ Sohbet geçmişi ve aktif görev durumu temizlendi.")
        return

    if raw_msg == "/status":
        task = active_tasks.get(user_id) or load_task_state(user_id)
        task_info = f"• Aktif Görev: {task.status} (Hedef: {task.goal[:50]}, Tur: {task.turns_used})" if task else "• Aktif Görev: Yok (Boşta)"
        try:
            hb = alfred.get_health() if alfred else {}
            alfred_st = f"✅ Online (Direct :7788, v{hb.get('version', '?')})" if hb.get("ok") else "❌ Offline"
        except Exception:
            alfred_st = "❌ Erişilemiyor"

        try:
            req = urllib.request.Request(f"{BRIDGE_API_URL}/health", method="GET")
            with urllib.request.urlopen(req, timeout=5) as r:
                ab = json.loads(r.read().decode())
                aider_st = "✅ Ready" if ab.get("aider_ready") else "❌ Offline"
        except Exception:
            aider_st = "❌ Erişilemiyor"

        await update.message.reply_text(
            f"📊 **Jeff System Status**\n"
            f"{task_info}\n"
            f"• Linux Sunucu (13.140.183.88): ✅ Online\n"
            f"• Alfred (Windows Direct :7788): {alfred_st}\n"
            f"• Aider (Bridge :7700): {aider_st}\n"
            f"• Model: {MODEL}\n"
            f"• Sohbet Hafızası: {len(get_history(user_id))} mesaj",
            parse_mode="Markdown"
        )
        return

    if raw_msg.lower() in ("dur", "iptal", "bırak", "vazgeç"):
        if user_id in active_tasks:
            del active_tasks[user_id]
        save_task_state(user_id)
        conversations[user_id] = []
        await update.message.reply_text("🛑 Görev iptal edildi ve durduruldu.")
        return

    # Task State Yönetimi
    active_task = active_tasks.get(user_id) or load_task_state(user_id)
    affirmative_words = ["evet", "uygula", "onay", "devam", "tamam", "başla", "yap", "yürüt", "ok", "yes", "go"]
    is_affirmative = any(raw_msg.lower().startswith(w) or raw_msg.lower() == w for w in affirmative_words)

    if active_task and active_task.status == "WAITING_FOR_APPROVAL":
        if is_affirmative:
            active_task.status = "IN_PROGRESS"
            active_task.completed_steps.append(f"APPROVED: {active_task.pending_action}")
            save_task_state(user_id)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] APPROVAL_GRANTED for: {active_task.pending_action}")
            add_to_history(user_id, "user", f"Onay verildi: {raw_msg}. Kaldığın yerden işlemi derhal tamamla.")
        else:
            active_task.status = "BLOCKED"
            save_task_state(user_id)
            await update.message.reply_text(f"🛑 Onay verilmediği için işlem durduruldu: {active_task.pending_action}")
            return
    elif active_task and active_task.status == "TASK_PAUSED":
        if is_affirmative:
            active_task.status = "IN_PROGRESS"
            active_task.turns_used = 0
            is_resumed = True
            save_task_state(user_id)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] TASK_RESUMED from pause checkpoint.")
            add_to_history(user_id, "user", f"Devam komutu verildi: {raw_msg}. Kaldığın yerden eksik kalan adımları tamamla.")
        else:
            add_to_history(user_id, "user", raw_msg)
    else:
        # Always ensure active_task is instantiated so it is NEVER None
        if not active_task or active_task.status in ("SUCCESS", "BLOCKED"):
            active_task = TaskState(req_id, raw_msg, user_id)
            active_tasks[user_id] = active_task
        save_task_state(user_id)
        add_to_history(user_id, "user", raw_msg)

        # Determine intent: Conversational Chat vs Real Action Task
        is_task = is_action_task(raw_msg, active_task)

        if not is_task:
            # FAST-PATH CHAT: Lightweight context, no tools payload, zero task loop overhead
            typing_task = asyncio.create_task(send_continuous_typing(update.message.chat))
            try:
                chat_system_prompt = build_system_prompt(is_task=False)
                messages = [{"role": "system", "content": chat_system_prompt}] + get_history(user_id)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] FAST_CHAT_CALL (msgs={len(messages)})", flush=True)
                raw_res = await call_antigravity(messages, include_tools=False)
                choices = raw_res.get("choices") or [{}]
                msg_obj = choices[0].get("message") or {}
                content = (msg_obj.get("content") or "").strip()
                if content:
                    add_to_history(user_id, "assistant", content=content)
                    active_task.status = "SUCCESS"
                    save_task_state(user_id)
                    await update.message.reply_text(content)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] FAST_CHAT_COMPLETE (len={len(content)})", flush=True)
                    return
                else:
                    await update.message.reply_text("👋 Buradayım kanka! Dinliyorum, nasıl yardımcı olabilirim?")
                    return
            except Exception as fe:
                print(f"[FAST_CHAT_ERROR] {fe}", flush=True)
                err_str = str(fe).lower()
                if "500" in err_str or "429" in err_str or "time" in err_str or "exhausted" in err_str:
                    await update.message.reply_text("⚠️ Model ağ geçidinde anlık bir gecikme oluştu. Tüm sistem servisleri ayakta, hemen tekrar deneyebilirsin.")
                else:
                    await update.message.reply_text("👋 Buradayım kanka, anlık bağlantı tazelendi. Mesajını tekrar iletir misin?")
                return
            finally:
                typing_task.cancel()

    # Safety Guard: Ensure active_task exists before entering autonomous continuation loop
    if not active_task:
        active_task = TaskState(req_id, raw_msg, user_id)
        active_tasks[user_id] = active_task
    save_task_state(user_id)
    typing_task = asyncio.create_task(send_continuous_typing(update.message.chat))
    status_indicator = TaskStatusIndicator(update.message)
    if is_resumed:
        await status_indicator.update(STAGE_RESUMING, force=True)
    else:
        await status_indicator.update(STAGE_THINKING)

    # Dinamik System Prompt (SOUL + USER + MEMORY + TOPOLOGY + PROTOCOL)
    if not active_task.system_prompt:
        active_task.system_prompt = build_system_prompt(is_task=True)
    current_system_prompt = active_task.system_prompt

    MAX_TOOL_TURNS = 25
    current_turn = 0
    final_text = ""
    photos_to_send = []
    executed_tool_summaries = []

    try:
        # ══════════════════════════════════════════════════════════════════
        # AUTONOMOUS CONTINUATION LOOP
        # ══════════════════════════════════════════════════════════════════
        while current_turn < MAX_TOOL_TURNS:
            current_turn += 1
            active_task.turns_used += 1
            messages = [{"role": "system", "content": current_system_prompt}] + get_history(user_id)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] [Turn {current_turn}] MODEL_DECISION (msgs={len(messages)})")

            raw_res = await call_antigravity(messages, include_tools=True)
            choices = raw_res.get("choices") or [{}]
            msg_obj = choices[0].get("message") or {}
            tool_calls = msg_obj.get("tool_calls")
            raw_content = (msg_obj.get("content") or "").strip()

            # Durum 1: Model doğrudan metin yanıtı verdi (Başka tool çağırmadı)
            if not tool_calls and raw_content:
                final_text = "Görev doğrulanmadı; durum korundu. " + raw_content
                active_task.status = "TASK_PAUSED"
                save_task_state(user_id)
                add_to_history(user_id, "assistant", content=final_text)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] [Turn {current_turn}] TASK_COMPLETE (len={len(final_text)})")
                break

            # Durum 2: Model tool_calls üretti
            assistant_thought = msg_obj.get("content") or ""
            add_to_history(user_id, "assistant", content=assistant_thought, tool_calls=tool_calls)
            stage_status = get_stage_status_for_tools(tool_calls)
            await status_indicator.update(stage_status)

            approval_needed = False
            for tc in (tool_calls or []):
                fn_name = tc.get("function", {}).get("name", "")
                raw_args = tc.get("function", {}).get("arguments", {})
                if isinstance(raw_args, dict):
                    fn_args = raw_args
                elif isinstance(raw_args, str):
                    try:
                        fn_args = json.loads(raw_args, strict=False)
                    except Exception:
                        try:
                            import ast
                            fn_args = ast.literal_eval(raw_args)
                            if not isinstance(fn_args, dict):
                                fn_args = {}
                        except Exception as pe:
                            print(f"[ARG_PARSE_ERROR] {fn_name}: {pe} for {raw_args[:100]}")
                            fn_args = {}
                else:
                    fn_args = {}

                call_sig = f"{fn_name}:{str(sorted(fn_args.items()))}"
                if call_sig == active_task.last_failed_sig:
                    active_task.consecutive_same_error += 1
                else:
                    active_task.consecutive_same_error = 0

                if active_task.consecutive_same_error >= 3:
                    out_text = f"⚠️ [LOOP_PREVENTION_BLOCKED]: '{fn_name}' aracı aynı parametrelerle 3 kez başarısız oldu. Bu yöntemi derhal bırak ve alternatif bir yaklaşım seç."
                    photo_file = None
                    was_rejected = True
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] [Turn {current_turn}] TOOL_CALL: {fn_name} with {str(fn_args)[:120]}")
                    out_text, photo_file, was_rejected = execute_tool_call(
                        fn_name, fn_args, user_message=raw_msg, has_active_task=True, task_obj=active_task
                    )

                if "[TOOL_RESULT: ERROR]" in out_text or "[TOOL_RESULT: EXCEPTION]" in out_text:
                    active_task.last_failed_sig = call_sig
                    active_task.failed_attempts += 1
                else:
                    active_task.last_failed_sig = ""

                if photo_file:
                    photos_to_send.append(photo_file)
                if not was_rejected:
                    executed_tool_summaries.append(f"🔧 {fn_name}")
                # Successful execution steps are recorded by execute_tool_call.

                print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] [Turn {current_turn}] TOOL_RESULT: {fn_name} (rejected={was_rejected}, out_len={len(out_text)})")
                add_to_history(user_id, "tool", content=out_text, tool_call_id=tc.get("id", ""))

                if fn_name == "request_human_approval":
                    approval_needed = True

            save_task_state(user_id)

            if approval_needed or active_task.status == "WAITING_FOR_APPROVAL":
                await status_indicator.update(STAGE_APPROVAL, force=True)
                final_text = (
                    f"⚠️ **İnsan Onayı Gerekiyor (Kırmızı Çizgi)**\n\n"
                    f"• **İşlem:** {active_task.pending_action}\n"
                    f"• **Sebep:** {active_task.pending_reason}\n\n"
                    f"Bu adımı onaylıyor musunuz? (Onay vermek için 'Evet' veya 'Uygula', iptal etmek için 'İptal' yazabilirsiniz.)"
                )
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] WAITING_FOR_APPROVAL paused loop.")
                break

            if active_task.status == "SUCCESS":
                final_text = out_text
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] TASK_COMPLETE via complete_task.")
                break

            if current_turn >= MAX_TOOL_TURNS and active_task.status != "SUCCESS":
                active_task.status = "TASK_PAUSED"
                save_task_state(user_id)
                final_text = (
                    f"⚠️ **Görev 25 Tur Sınırına Ulaştı ve Duraklatıldı (TASK_PAUSED)**\n\n"
                    f"• **Hedef:** {active_task.goal}\n"
                    f"• **Tamamlanan Adımlar:** {', '.join(active_task.completed_steps[-5:])}\n"
                    f"• **Durum:** Tamamlama ve doğrulama koşulları henüz tam sağlanmadığı için KESİNLİKLE 'tamamlandı' sayılmadı.\n\n"
                    f"Task state korundu. Kalan aşamalara devam etmek için 'Devam et' yazmanız yeterlidir."
                )
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] TOOL_LIMIT reached ({MAX_TOOL_TURNS} turns). State saved as TASK_PAUSED.")
                break

        # ══════════════════════════════════════════════════════════════════
        # SYNTHESIS & FINAL RESPONSE
        # ══════════════════════════════════════════════════════════════════
        if not final_text:
            await status_indicator.update(STAGE_SYNTHESIS)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] FINAL_SYNTHESIS: Generating conclusive summary...")
            synthesis_steering = {
                "role": "user",
                "content": (
                    "Yalnız araç çıktılarıyla kanıtlanan adımları bildir; eksikleri tamamlandı sayma. Başka araç çağırma.\n"
                    "Elde ettiğin tüm bulguları, yapılan değişiklikleri ve doğrulama kanıtlarını net, eksiksiz ve doğrudan Türkçe sentezle.\n"
                    "Eğer eksik kalan veya ek onay bekleyen bir nokta varsa dürüstçe belirt."
                )
            }
            synthesis_messages = [{"role": "system", "content": current_system_prompt}] + get_history(user_id) + [synthesis_steering]
            final_res = await call_antigravity(synthesis_messages, include_tools=False)
            final_choices = final_res.get("choices") or [{}]
            final_msg = final_choices[0].get("message") or {}
            synthesized_text = (final_msg.get("content") or "").strip()

            if synthesized_text:
                final_text = synthesized_text
                add_to_history(user_id, "assistant", content=final_text)
            else:
                final_text = "Görev doğrulanamadı; kayıt korundu."

        save_task_state(user_id)
        if active_task.status == "SUCCESS":
            if user_id in active_tasks:
                del active_tasks[user_id]
            save_task_state(user_id)

        for pf in photos_to_send:
            try:
                with open(pf, "rb") as img:
                    await update.message.reply_photo(photo=img, caption="🖥️ Masaüstü Ekran Görüntüsü")
            except Exception as pe:
                print(f"Fotoğraf gönderme hatası: {pe}")

        response_text = final_text

    except Exception as exc:
        active_task.status = "TASK_PAUSED"
        save_task_state(user_id)
        import traceback
        traceback.print_exc()
        err_str = str(exc).lower()
        if "500" in err_str or "429" in err_str or "time" in err_str or "exhausted" in err_str:
            response_text = (
                "⚠️ Model ağ geçidinde (Gateway) anlık bir kota veya yoğunluk oluştu. "
                "Görev durumu ve kanıtları kaydedildi; tamamlanmış sayılmadı.\n\n"
                "Devam isteğiyle kaydedilen görevden sürdürülebilir."
            )
        else:
            response_text = f"❌ Bir hata oluştu: {str(exc)}"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [REQ:{req_id}] ERROR: {str(exc)}")
    finally:
        typing_task.cancel()

    reused = await status_indicator.finalize(response_text, MAX_MESSAGE_LENGTH)
    if not reused:
        if len(response_text) > MAX_MESSAGE_LENGTH:
            for i in range(0, len(response_text), MAX_MESSAGE_LENGTH):
                await update.message.reply_text(response_text[i:i+MAX_MESSAGE_LENGTH])
        else:
            await update.message.reply_text(response_text)
    else:
        if len(response_text) > MAX_MESSAGE_LENGTH:
            for i in range(MAX_MESSAGE_LENGTH, len(response_text), MAX_MESSAGE_LENGTH):
                await update.message.reply_text(response_text[i:i+MAX_MESSAGE_LENGTH])

# ── Main ────────────────────────────────────────────────
def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN bulunamadı!")

    # Telegram sahipliği tek elde: hermes-gateway sahipteyse bu bot bekleme modunda kalır (409 polling çakışması olmasın)
    _owner_file = Path("/home/hermes/.hermes/telegram-owner")
    if _owner_file.exists() and _owner_file.read_text(encoding="utf-8").strip() == "gateway":
        print("ℹ️ Telegram sahipliği hermes-gateway'de — bu bot bekleme modunda, polling yok.")
        while True:
            time.sleep(3600)

    print("🤖 Telegram Hermes Bot v4.1 (Identity + Memory + Runtime Stack) başlatılıyor...")
    print(f"   Model: {MODEL}")
    print(f"   Bridge API (:7700): {BRIDGE_API_URL}")
    print(f"   Alfred Direct (:7788): {'Hazır' if alfred else 'Erişilemedi'}")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(15)
        .pool_timeout(15)
        .build()
    )

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # Caption'siz dosya/fotoğraf/ses de yakalanır — aksi halde handler hiç tetiklenmiyordu (dosya atınca tepki yok)
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.VOICE | filters.AUDIO | filters.VIDEO,
        handle_message,
    ))
    app.add_handler(CommandHandler("start", handle_message))
    app.add_handler(CommandHandler("clear", handle_message))
    app.add_handler(CommandHandler("status", handle_message))
    app.add_handler(CommandHandler("help", handle_message))

    print("✅ Bot tam kimlik, hafıza, topoloji ve Linux/Windows icra motoruyla donatıldı!")
    app.run_polling(drop_pending_updates=False)

if __name__ == "__main__":
    main()
