"""Durable, single-use action boundary shared by REST, bridge and Telegram."""
import hashlib
import ipaddress
import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager


def fingerprint(action, params):
    return hashlib.sha256(json.dumps([action, params], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def allowed_ip(address, allowlist):
    try:
        ip = ipaddress.ip_address(address)
        return ip.is_loopback or any(ip == ipaddress.ip_address(x) for x in allowlist)
    except ValueError:
        return False


READ_ACTIONS = {
    'ping', 'window_list', 'gui_coords', 'screenshot', 'vision_grounding',
    'browser_read', 'pilot_status', 'read', 'read_file', 'file_read',
    'read_file_content', 'file_list', 'list_files', 'list_dir', 'dir_list',
    'file_exists', 'path_exists', 'file_stat', 'health'
}
GUI_ACTIONS = {'window_focus', 'gui_click', 'gui_drag', 'gui_scroll', 'gui_type', 'screenshot',
               'vision_grounding', 'browser_open', 'browser_read', 'browser_act', 'browser_session',
               'pilot_run_session', 'youtube_play', 'whatsapp_send', 'whatsapp_draft'}

DESTRUCTIVE_COMMAND_PATTERNS = [
    "rmdir /s", "rd /s",
    "del /f /s", "del /s /q", "del /f /q c:\\",
    "format ", "format.com",
    "drop database", "drop table", "truncate table",
    "remove-item -recurse", "remove-item -force",
    "rm -rf /", "rm -rf ~", "rm -rf c:",
    "shutdown", "stop-computer",
    "diskpart", "format-volume"
]

FINANCIAL_KEYWORDS = [
    "odeme", "payment", "purchase", "satinal", "checkout", "transfer_money"
]

# Adlandırılmış eylemler (whatsapp_send vb.) onaya bağlansa da, jenerik
# gui_click/gui_type primitifleri aynı etkiyi (bir pencereye Enter basıp
# mesaj göndermek) onay kapısını hiç görmeden üretebilir — bkz.
# knowledge/concepts/approval-gate-composability-gap.md. Bu liste, hangi
# pencereler odaktayken "gönderim" niyetli jenerik girdinin de onay
# gerektireceğini tanımlar. Yeni bir gönderim yüzeyi (Instagram DM,
# Twitter/X compose vb.) Pablo'ya eklendiğinde buraya da eklenmeli.
SENSITIVE_SEND_WINDOW_PATTERNS = [
    "whatsapp", "instagram", "gmail", "outlook", "e-posta", "yeni ileti", "compose", "linkedin",
    "messenger", "facebook", "telegram", "twitter", " / x", "direct",
]
# Tıklanan veya seçilen öğenin adında bunlardan biri geçiyorsa, hassas bir pencerede bu bir GÖNDERİM jestidir.
SEND_GESTURE_WORDS = (
    "gönder", "gonder", "send", "paylaş", "paylas", "share", "post", "tweet", "yayınla", "yayinla",
    "publish", "reply", "yanıtla", "yanitla",
)
SENSITIVE_SEND_URL_PATTERNS = (
    "instagram.com", "mail.google.com", "outlook.", "web.whatsapp.com", "x.com", "twitter.com",
    "linkedin.com", "facebook.com", "messenger.com", "web.telegram.org",
)


def _foreground_window_title() -> str:
    try:
        import win32gui
        return win32gui.GetWindowText(win32gui.GetForegroundWindow()) or ""
    except Exception:
        return ""


def _is_send_gesture(action: str, params: dict) -> str:
    """Bir tıklama / tarayıcı eylemi, hassas bir yüzeyde GÖNDERİM etkisi üretiyorsa nedenini döndürür, yoksa ''.
    Okuma, gezinme, pencere değiştirme ve adsız tıklamalar bu kurala takılmaz (otonom kalır)."""
    if action not in ("gui_click", "browser_act"):
        return ""
    if action == "gui_click":
        label = str(params.get("control_name") or params.get("name") or "").lower()
        context = str(params.get("window_title") or params.get("window") or "").lower() or _foreground_window_title().lower()
        url = ""
        pressed_enter = False
    else:
        act = str(params.get("type") or params.get("action") or "click").lower()
        if act not in ("click", "press", "submit", "type", "fill"):
            return ""
        label = " ".join(str(params.get(k) or "") for k in ("selector", "target", "value", "text")).lower()
        context = _foreground_window_title().lower()
        url = str(params.get("url") or "").lower()
        pressed_enter = act in ("press", "submit") and any(w in label for w in ("enter", "return", "\n"))
        pressed_enter = pressed_enter or bool(params.get("enter") or params.get("submit"))
    sensitive = any(p in context for p in SENSITIVE_SEND_WINDOW_PATTERNS) or any(p in url for p in SENSITIVE_SEND_URL_PATTERNS)
    if not sensitive:
        return ""
    if any(w in label for w in SEND_GESTURE_WORDS):
        return f"GONDERIM_JESTI: hassas yüzeyde ('{context or url}') '{label.strip()[:40]}' Bilal Ergene onayı gerektirir."
    if pressed_enter:
        return f"GONDERIM_JESTI: hassas yüzeyde ('{context or url}') Enter ile gönderim Bilal Ergene onayı gerektirir."
    return ""


def is_approval_required(action: str, params: dict) -> tuple:
    """
    CYBERGENE APPROVAL GATE — Kırmızı Çizgiler:
    (1) Kamuoyuna açık paylaşım (sosyal medya paylaşımı, tweet, post vb.)
    (2) Yeni/soğuk kişiye ilk mesaj (WhatsApp, DM) - is_new_contact: True
    (3) Yıkıcı dosya veya sistem işlemi (rmdir /s, del /s, format, drop table vb.)
    (4) Finansal harcama / taahhüt (ödeme, satın alma vb.)
    
    Zararsız okuma, dosya inceleme (read, file_list, Get-Content, dir, type),
    durum sorgulama, pencere odağı ve güvenli komutlar kesinlikle onay kapısına takılmadan OTONOM icra edilir.
    """
    if not isinstance(params, dict):
        params = {}

    # Açık onay zorlama bayrağı
    if params.get("require_approval") or params.get("force_approval"):
        return True, "ZORUNLU_ONAY: Gönderen tarafından açık onay talep edildi."

    # 1. Kamuoyuna açık paylaşım (Platform / Sosyal Medya)
    if action in ("social_post", "twitter_post", "instagram_post", "tweet_post", "publish_post"):
        return True, "KAMUOYUNA_ACIK_PAYLASIM: Platform paylaşımı için Bilal Ergene onayı zorunludur."
    if params.get("public_post") or params.get("is_public"):
        return True, "KAMUOYUNA_ACIK_PAYLASIM: Kamuya açık paylaşım için Bilal Ergene onayı zorunludur."

    # 2. Yeni kişiye ilk mesaj (Önceden konuşulmamış / soğuk numara)
    if action in ("whatsapp_send", "whatsapp_draft", "dm_send", "send_message"):
        if bool(params.get("is_new_contact") or params.get("new_recipient")):
            return True, "YENI_KISIYE_MESAJ: Yeni/önceden konuşulmamış kişiye mesaj için Bilal Ergene onayı zorunludur."

    # 2b. Jenerik primitifle onay kapısının dolanılması: hassas bir pencere
    # (WhatsApp vb.) odaktayken Enter'a basmak, adlandırılmış whatsapp_send
    # eyleminin ürettiği etkiyle aynıdır ve aynı şekilde onay gerektirir —
    # eylem adı "gui_type" olsa bile.
    if action == "gui_type" and (params.get("enter") or str(params.get("text", "")) in ("\n", "\r")):
        title = _foreground_window_title().lower()
        if any(p in title for p in SENSITIVE_SEND_WINDOW_PATTERNS):
            return True, f"HASSAS_PENCEREDE_GONDERIM: '{title}' odaktayken Enter ile gönderim Bilal Ergene onayı gerektirir."

    # 2c. Aynı dolanma, tıklama ve tarayıcı otomasyonu ile: "Gönder", "Paylaş", "Yayınla" gibi adlı bir düğme ya da
    # Enter, hassas bir yüzeyde (WhatsApp, Instagram, e-posta, X, LinkedIn...) adlandırılmış gönderim eylemiyle
    # aynı etkiyi üretir.
    gesture = _is_send_gesture(action, params)
    if gesture:
        return True, gesture

    # 3. Yıkıcı dosya / sistem işlemleri
    if action == "shell":
        cmd = str(params.get("command") or params.get("cmd") or "").strip().lower()
        for dk in DESTRUCTIVE_COMMAND_PATTERNS:
            if dk in cmd:
                return True, f"YIKICI_SISTEM_ISLEMI: '{dk}' komutu Bilal Ergene onayı gerektirir."

    if action in ("file_delete", "delete_file", "dir_remove"):
        return True, f"YIKICI_DOSYA_ISLEMI: Dosya/dizin silme ({action}) Bilal Ergene onayı gerektirir."

    # 4. Finansal harcama / taahhüt
    if action in ("payment", "checkout", "buy", "transfer_money"):
        return True, "FINANSAL_ISLEM: Finansal işlem Bilal Ergene onayı gerektirir."

    text = str(params.get("text") or params.get("content") or "").lower()
    for fk in FINANCIAL_KEYWORDS:
        if fk in text:
            return True, f"FINANSAL_ISLEM: Parametrelerde finansal işlem tespit edildi ('{fk}'). Bilal Ergene onayı zorunludur."

    return False, "OK"


class TaskGuard:
    def __init__(self, path, actions, owner, desktop_ready, clock=time.time, ttl=300):
        self.path, self.actions, self.owner = str(path), actions, str(owner or '')
        self.desktop_ready, self.clock, self.ttl = desktop_ready, clock, ttl
        self.lock = threading.RLock()
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, digest TEXT, action TEXT, params TEXT, status TEXT, response TEXT, approval TEXT, expires REAL, consumed INTEGER DEFAULT 0)')
            db.execute('CREATE TABLE IF NOT EXISTS outbox (id TEXT PRIMARY KEY, payload TEXT)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def response(self, rid, status, **kw):
        return dict(request_id=rid, task_id=rid, status=status, ok=status == 'SUCCESS', **kw)

    def store(self, db, rid, result):
        db.execute('UPDATE requests SET status=?, response=? WHERE id=?', (result['status'], json.dumps(result), rid))
        return result

    def get(self, rid):
        with self.connect() as db:
            row = db.execute('SELECT response FROM requests WHERE id=?', (rid,)).fetchone()
            return json.loads(row[0]) if row else self.response(rid, 'NOT_FOUND', error='Unknown request')

    def queue_result(self, payload):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO outbox VALUES (?,?)', (payload['task_id'], json.dumps(payload)))

    def flush_results(self, sender):
        with self.connect() as db:
            rows = db.execute('SELECT id,payload FROM outbox').fetchall()
        for rid, raw in rows:
            try:
                sender(json.loads(raw))
            except Exception:
                continue
            with self.connect() as db:
                db.execute('DELETE FROM outbox WHERE id=? AND payload=?', (rid, raw))

    def execute(self, action, params, request_id=None):
        rid = request_id or str(uuid.uuid4())
        if not isinstance(rid, str) or not rid or len(rid) > 128 or not isinstance(params, dict):
            return self.response(str(rid)[:128], 'ERROR', error='Invalid request')
        params = json.loads(json.dumps(params))
        digest = fingerprint(action, params)
        with self.lock, self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT digest,response FROM requests WHERE id=?', (rid,)).fetchone()
            if row:
                if row[0] != digest:
                    return self.response(rid, 'CONFLICT', error='Request ID reused with changed action/params')
                return json.loads(row[1])
            result = self.response(rid, 'IN_PROGRESS')
            db.execute('INSERT INTO requests(id,digest,action,params,status,response) VALUES(?,?,?,?,?,?)',
                       (rid, digest, action, json.dumps(params), result['status'], json.dumps(result)))
            # Kırmızı Çizgi Kontrolü (Approval Gate)
            needs_approval, reason = is_approval_required(action, params)
            if needs_approval:
                aid = str(uuid.uuid4())
                result = self.response(rid, 'APPROVAL_REQUIRED', approval_id=aid, reason=reason, error=f'Owner approval required: {reason}')
                db.execute('UPDATE requests SET approval=?,expires=? WHERE id=?', (aid, self.clock() + self.ttl, rid))
                return self.store(db, rid, result)

            if action not in self.actions:
                return self.store(db, rid, self.response(rid, 'ERROR', error='Unknown action'))
            db.commit()  # Persist claim BEFORE executing anything.
        return self._run(rid, action, params)

    def approve(self, approval_id, user_id, chat_id, reject=False):
        with self.lock, self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT id,action,params,digest,expires,consumed,status FROM requests WHERE approval=?', (approval_id,)).fetchone()
            if not row:
                return self.response('', 'REJECTED', error='Unknown approval')
            rid, action, raw, digest, expires, consumed, status = row
            if not self.owner or str(user_id) != self.owner or str(chat_id) != self.owner:
                return self.response(rid, 'REJECTED', error='Wrong approver or chat')
            if consumed or status != 'APPROVAL_REQUIRED':
                return self.response(rid, 'REJECTED', error='Approval already consumed')
            params = json.loads(raw)
            if self.clock() > expires or fingerprint(action, params) != digest or reject:
                db.execute('UPDATE requests SET consumed=1 WHERE id=?', (rid,))
                return self.store(db, rid, self.response(rid, 'REJECTED', error='Expired, changed or rejected approval'))
            db.execute('UPDATE requests SET consumed=1 WHERE id=?', (rid,))
            self.store(db, rid, self.response(rid, 'IN_PROGRESS'))
            db.commit()
        return self._run(rid, action, params)

    def _run(self, rid, action, params):
        # One desktop action at a time; repeat the desktop check at execution time.
        with self.lock:
            try:
                if action in GUI_ACTIONS and not self.desktop_ready():
                    result = self.response(rid, 'BLOCKED', error='Desktop locked, active or unavailable')
                else:
                    raw = self.actions[action](params)
                    if not isinstance(raw, dict):
                        raw = dict(ok=False, error='Invalid action response')
                    inner = raw.get('result') if isinstance(raw.get('result'), dict) else {}
                    ok = raw.get('ok') is True and inner.get('ok', True) is not False and inner.get('exit_code', 0) == 0
                    result = self.response(rid, 'SUCCESS' if ok else 'ERROR', result=raw.get('result'),
                                           error=None if ok else raw.get('error', 'Action failed'))
            except Exception as exc:
                result = self.response(rid, 'ERROR', error=type(exc).__name__)
            with self.connect() as db:
                return self.store(db, rid, result)


AMBIGUOUS_TARGETS = {'button', 'div', 'a', 'span', 'input', 'p', 'h1', 'h2', 'h3', 'header', 'footer', 'main', 'section', 'article', 'body'}

def validate_target_specificity(target: str) -> tuple:
    if not target or not isinstance(target, str):
        return False, "BLOCKED_AMBIGUOUS_TARGET: Target is empty or invalid"
    clean = target.strip().lower()
    if clean in AMBIGUOUS_TARGETS or clean.startswith('.btn') or len(clean) < 3:
        return False, f"BLOCKED_AMBIGUOUS_TARGET: Generic target '{clean}' rejected. Specific role, aria-label, data-testid or text selector required."
    return True, "OK"
