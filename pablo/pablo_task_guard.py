"""Durable, single-use action boundary shared by REST, bridge and Telegram."""
import hashlib
import ipaddress
import json
import math
import re
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from contextlib import contextmanager
from pablo_local_drafts import LocalDraftStore, DraftError, expectation
from pablo_antigravity import ALIASES as ANTIGRAVITY_ALIASES, prepare as prepare_antigravity
from pablo_approval_client import action_binding, ApprovalUnavailable


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
GUI_ACTIONS.update(ANTIGRAVITY_ALIASES)
CLOSED_WORK_STATUSES = {'SUCCESS', 'REJECTED', 'EXPIRED', 'NEEDS_REVALIDATION', 'CANCELLED'}

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


def _coordinate_target(params):
    """Read the actual control under a point; never trust a caller-supplied label."""
    try:
        import uiautomation as auto
        with auto.UIAutomationInitializerInThread():
            control = auto.ControlFromPoint(int(params['x']), int(params['y']))
            if control is not None:
                window = control.GetTopLevelControl()
                return {'name': control.Name or '', 'window': window.Name if window else ''}
    except Exception:
        pass
    return {'name': '', 'window': ''}


def _shell_approval_reason(command):
    """Recognise destructive operations independent of argument order.

    This is a policy classifier, not a sandbox for arbitrary programs.
    """
    cmd = command.strip().lower()
    for pattern in DESTRUCTIVE_COMMAND_PATTERNS:
        if pattern in cmd:
            return f"YIKICI_SISTEM_ISLEMI: '{pattern}' Bilal Ergene onayı gerektirir."
    if re.search(r'\b(?:remove-item|erase|del|rmdir|rd|rm|unlink|remove-directory)\b', cmd):
        return "YIKICI_SISTEM_ISLEMI: silme komutu Bilal Ergene onayı gerektirir."
    if re.search(r'\.(?:unlink|remove|rmtree|rmdir)\s*\(', cmd):
        return "YIKICI_SISTEM_ISLEMI: program içinden silme Bilal Ergene onayı gerektirir."
    if re.search(r'\b(?:powershell|pwsh)(?:\.exe)?\b.*\s-(?:enc\w*|e)\b', cmd):
        return "BELIRSIZ_KOMUT: kodlanmış komut Bilal Ergene onayı gerektirir."
    if re.search(r'\b(?:exec|eval)\s*\(|\b(?:invoke-expression|iex)\b', cmd):
        return "BELIRSIZ_KOMUT: dinamik kod çalıştırma Bilal Ergene onayı gerektirir."
    if re.search(r'\b(?:pyautogui|auto|win32api)\.(?:click|press|hotkey|sendkeys|keybd_event)\s*\(', cmd):
        return "DOLAYLI_GUI: komut üzerinden tıklama/gönderim Bilal Ergene onayı gerektirir."
    return ""


def _is_send_gesture(action: str, params: dict) -> str:
    """Bir tıklama / tarayıcı eylemi, hassas bir yüzeyde GÖNDERİM etkisi üretiyorsa nedenini döndürür, yoksa ''.
    Hassas yüzeyde çözümlenemeyen koordinat tıklaması da onaya gider."""
    if action not in ("gui_click", "browser_act"):
        return ""
    if action == "gui_click":
        label = str(params.get("control_name") or params.get("name") or "").lower()
        context = ' '.join((_foreground_window_title(), str(params.get("window_title") or params.get("window") or ''))).lower()
        unknown_point = False
        if params.get('x') is not None and params.get('y') is not None:
            observed = _coordinate_target(params)
            label = observed['name'].lower()
            context += ' ' + observed['window'].lower()
            unknown_point = not bool(label)
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
    if action == 'gui_click' and unknown_point:
        return "BELIRSIZ_GONDERIM_HEDEFI: hassas yüzeyde tıklama hedefi okunamadı; Bilal Ergene onayı gerektirir."
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
    if action in ('local_draft', 'local_draft_plan'):
        # The durable guard validates this bounded, private draft contract first.
        return False, 'LOCAL_DRAFT_ONLY'
    if action in ANTIGRAVITY_ALIASES:
        return True, 'OPAQUE_EXECUTION: Antigravity script/tool side effects require an input-bound owner decision.'

    # Açık onay zorlama bayrağı
    if params.get("require_approval") or params.get("force_approval"):
        return True, "ZORUNLU_ONAY: Gönderen tarafından açık onay talep edildi."

    # 1. Kamuoyuna açık paylaşım (Platform / Sosyal Medya)
    if action in ("social_post", "twitter_post", "instagram_post", "tweet_post", "publish_post"):
        return True, "KAMUOYUNA_ACIK_PAYLASIM: Platform paylaşımı için Bilal Ergene onayı zorunludur."
    if params.get("public_post") or params.get("is_public"):
        return True, "KAMUOYUNA_ACIK_PAYLASIM: Kamuya açık paylaşım için Bilal Ergene onayı zorunludur."

    if action == 'marketing_playbook' and params.get('playbook') == 'instagram_bio':
        return True, "KAMUOYUNA_ACIK_PAYLASIM: Profil değişikliği Bilal Ergene onayı gerektirir."
    if (action == 'marketing_playbook' and params.get('playbook') == 'deliver_campaign'
            and params.get('simulated', True) is not True):
        return True, "DIS_TEMAS: Gerçek kampanya gönderimi Bilal Ergene onayı gerektirir."
    if action in ('create_account', 'delete_account', 'close_account', 'open_account'):
        return True, "HESAP_ISLEMI: Hesap açma/kapatma Bilal Ergene onayı gerektirir."

    # 2. Yeni kişiye ilk mesaj (Önceden konuşulmamış / soğuk numara)
    if action in ("whatsapp_send", "dm_send", "send_message"):
        # Only an explicit boolean false identifies an existing contact.
        # Missing, string-valued or contradictory flags must not bypass approval.
        flags = [params[k] for k in ('is_new_contact', 'new_recipient') if k in params]
        if not flags or any(flag is not False for flag in flags):
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
        reason = _shell_approval_reason(cmd)
        if reason:
            return True, reason

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
    def __init__(self, path, actions, owner, desktop_ready, clock=time.time, ttl=300, approvals=None):
        self.path, self.actions, self.owner = str(path), actions, str(owner or '')
        self.desktop_ready, self.clock, self.ttl = desktop_ready, clock, ttl
        self.approvals=approvals
        self.local_drafts = LocalDraftStore(Path(self.path).parent / 'verified-drafts')
        self.lock = threading.RLock()
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, digest TEXT, action TEXT, params TEXT, status TEXT, response TEXT, approval TEXT, expires REAL, consumed INTEGER DEFAULT 0)')
            db.execute('CREATE TABLE IF NOT EXISTS outbox (id TEXT PRIMARY KEY, payload TEXT)')
            for name,definition in (('created_at','REAL'),('canonical_claim','TEXT'),
                                    ('updated_at','REAL'),('work_phase','TEXT'),
                                    ('deadline_at','REAL'),('observation_after','REAL'),('parent_id','TEXT')):
                if name not in {r[1] for r in db.execute('PRAGMA table_info(requests)')}:
                    db.execute('ALTER TABLE requests ADD COLUMN '+name+' '+definition)
            db.execute('CREATE TABLE IF NOT EXISTS work_events (seq INTEGER PRIMARY KEY, request_id TEXT NOT NULL, phase TEXT NOT NULL, status TEXT NOT NULL, observed_at REAL NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS work_plan_signals (request_id TEXT NOT NULL,step_name TEXT NOT NULL,input_digest TEXT NOT NULL,signal_key TEXT NOT NULL,actor_kind TEXT NOT NULL,source TEXT NOT NULL,recorded_at REAL NOT NULL,PRIMARY KEY(request_id,step_name))')
            db.execute('CREATE TABLE IF NOT EXISTS work_history (request_id TEXT PRIMARY KEY,archived_at REAL NOT NULL,reason TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS work_interruptions (request_id TEXT PRIMARY KEY,process_started_at REAL NOT NULL,detected_at REAL NOT NULL)')
            # Quiet legacy terminal failures; their outcome remains unverified.
            # Do not infer their age, archive pending authority or hide ambiguity.
            db.execute("INSERT OR IGNORE INTO work_history SELECT id,?,'legacy_terminal_failure_outcome_unverified' FROM requests r WHERE created_at IS NULL AND status IN ('ERROR','BLOCKED','FAILED') AND coalesce(approval,'')='' AND coalesce(canonical_claim,'')='' AND parent_id IS NULL AND NOT EXISTS (SELECT 1 FROM outbox o WHERE o.id=r.id)", (self.clock(),))
            for table in ('work_events', 'work_plan_signals', 'work_history', 'work_interruptions'):
                for operation in ('UPDATE', 'DELETE'):
                    db.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT, 'work history is append-only'); END")

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

    def note_restart(self, process_started_at):
        """Called only by the sole bound node before any executor starts.

        Preserve original rows. An old generic claim has no result contract;
        publish uncertainty, never replay or assert it is still executing.
        Undated legacy records cannot be assigned to a runtime this way.
        """
        if (type(process_started_at) not in (int,float) or not math.isfinite(process_started_at)
                or not 0 < process_started_at <= self.clock()):
            raise ValueError('Invalid node startup instant')
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO work_interruptions SELECT id,?,? FROM requests WHERE status='IN_PROGRESS' AND action NOT IN ('local_draft','local_draft_plan') AND created_at IS NOT NULL AND created_at<?",(process_started_at,self.clock(),process_started_at))

    def _recorded(self, db, rid, raw):
        result=json.loads(raw)
        receipt=db.execute('SELECT process_started_at,detected_at FROM work_interruptions WHERE request_id=?',(rid,)).fetchone()
        if receipt and result['status']=='IN_PROGRESS':
            result.update(recorded_status='IN_PROGRESS',status='OUTCOME_UNKNOWN',ok=False,outcome_verified=False,
                          error='Previous runtime ended without an outcome receipt; do not replay',
                          runtime_interruption={'process_started_at':receipt[0],'detected_at':receipt[1]})
        return result

    def store(self, db, rid, result):
        row = db.execute('SELECT action,status,response FROM requests WHERE id=?', (rid,)).fetchone()
        if row and row[0] == 'local_draft_plan' and row[1] == 'CANCELLED':
            return json.loads(row[2])
        # An independent recovery observation may have closed this request while
        # another process was finishing its original writer. Never regress it.
        if (row and row[0] in ('local_draft', 'local_draft_plan') and row[1] == 'SUCCESS'
                and not (row[0] == 'local_draft_plan' and result['status'] == 'RECOVERY_BLOCKED')):
            return json.loads(row[2])
        db.execute('UPDATE requests SET status=?, response=?,updated_at=? WHERE id=?', (result['status'], json.dumps(result), self.clock(), rid))
        phase = result.get('work', {}).get('phase') if row and row[0] == 'local_draft_plan' else None
        self._phase(db, rid, phase or self._status_phase(result['status']), result['status'])
        return result

    @staticmethod
    def _status_phase(status):
        if status == 'SUCCESS':
            return 'completed'
        if status in CLOSED_WORK_STATUSES:
            return 'closed'
        if status == 'IN_PROGRESS':
            return 'claimed'
        if status == 'APPROVAL_REQUIRED':
            return 'waiting_for_owner'
        return 'needs_review'

    def _phase(self, db, rid, phase, status=None):
        row = db.execute('SELECT work_phase,status FROM requests WHERE id=?', (rid,)).fetchone()
        if row is None:
            return
        if row[1] == 'SUCCESS' and phase != 'completed':
            return
        if row[0] == phase:
            last = db.execute('SELECT status FROM work_events WHERE request_id=? ORDER BY seq DESC LIMIT 1', (rid,)).fetchone()
            if last and last[0] == (status or row[1]):
                return
        now = self.clock()
        db.execute('UPDATE requests SET work_phase=?,updated_at=? WHERE id=?', (phase, now, rid))
        db.execute('INSERT INTO work_events(request_id,phase,status,observed_at) VALUES(?,?,?,?)',
                   (rid, phase, status or row[1], now))

    def work_status(self, rid):
        """One redacted record; stored task input and customer text stay private."""
        with self.connect() as db:
            row = db.execute('SELECT action,status,created_at,updated_at,work_phase,deadline_at,observation_after FROM requests WHERE id=?', (rid,)).fetchone()
            if row is None:
                return {'request_id': rid, 'status': 'NOT_FOUND', 'open': False}
            action, status, created, updated, phase, deadline, after = row
            if action == 'local_draft_plan':
                from pablo_work_plans import WorkPlans
                return WorkPlans(self).view(rid)
            interruption=db.execute('SELECT process_started_at,detected_at FROM work_interruptions WHERE request_id=?',(rid,)).fetchone()
            recorded_status=status
            if interruption and status=='IN_PROGRESS':
                status,phase='OUTCOME_UNKNOWN','outcome_unknown_after_restart'
            phase = phase if interruption and recorded_status=='IN_PROGRESS' else ((phase or 'legacy_unknown') if status == 'IN_PROGRESS' else self._status_phase(status))
            if status in CLOSED_WORK_STATUSES:
                next_step, waiting_for = 'none', None
            elif status == 'APPROVAL_REQUIRED':
                next_step, waiting_for = 'owner_decision', 'owner'
            elif action == 'local_draft':
                next_step, waiting_for = 'observe_file_without_writing', 'file_evidence'
            else:
                next_step, waiting_for = 'inspect_outcome_without_replay', 'outcome_evidence'
            events = [dict(seq=r[0], phase=r[1], status=r[2], observed_at=r[3]) for r in
                      db.execute('SELECT seq,phase,status,observed_at FROM work_events WHERE request_id=? ORDER BY seq DESC LIMIT 20', (rid,))]
            history = db.execute('SELECT archived_at,reason FROM work_history WHERE request_id=?', (rid,)).fetchone()
        return dict(request_id=rid, action=action, status=status, phase=phase, open=status not in CLOSED_WORK_STATUSES,
                    next_step=next_step, waiting_for=waiting_for, created_at=created, updated_at=updated,
                    deadline_at=deadline, deadline_known=deadline is not None,
                    overdue=deadline is not None and deadline < self.clock() and status not in CLOSED_WORK_STATUSES,
                    observation_after=after, automatic_replay=False, events=list(reversed(events)),
                    history_only=history is not None, archived_at=history[0] if history else None,
                    archive_reason=history[1] if history else None,
                    recorded_status=recorded_status,
                    runtime_interruption=({'process_started_at':interruption[0],'detected_at':interruption[1]}
                                          if interruption and recorded_status=='IN_PROGRESS' else None))

    def work_snapshot(self, limit=100, offset=0, include_history=False):
        limit, offset = max(1, min(int(limit), 100)), max(0, int(offset))
        selection = "parent_id IS NULL AND status NOT IN ('SUCCESS','REJECTED','EXPIRED','NEEDS_REVALIDATION','CANCELLED')"
        if not include_history:
            selection += ' AND NOT EXISTS (SELECT 1 FROM work_history h WHERE h.request_id=requests.id)'
        with self.connect() as db:
            total = db.execute('SELECT count(*) FROM requests WHERE ' + selection).fetchone()[0]
            history = db.execute("SELECT count(*) FROM work_history h JOIN requests r ON r.id=h.request_id WHERE r.status NOT IN ('SUCCESS','REJECTED','EXPIRED','NEEDS_REVALIDATION','CANCELLED')").fetchone()[0]
            ids = [r[0] for r in db.execute('SELECT id FROM requests WHERE ' + selection + ' ORDER BY coalesce(created_at,0),id LIMIT ? OFFSET ?', (limit, offset))]
        return {'open_count': total, 'items': [self.work_status(rid) for rid in ids],
                'next_offset': offset + len(ids) if offset + len(ids) < total else None,
                'observed_at': self.clock(), 'automatic_replay': False, 'history_open_count': history,
                'total_open_and_history': total if include_history else total + history,
                'includes_history': bool(include_history)}

    def reconcile(self, rid):
        """Observe the immutable local draft only. Never call an action/writer."""
        with self.connect() as db:
            kind = db.execute('SELECT action FROM requests WHERE id=?', (rid,)).fetchone()
        if kind and kind[0] == 'local_draft_plan':
            from pablo_work_plans import WorkPlans
            return WorkPlans(self).advance(rid, allow_new=False)
        with self.lock, self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT action,params,digest,status,response,observation_after FROM requests WHERE id=?', (rid,)).fetchone()
            if row is None:
                return self.response(rid, 'NOT_FOUND', error='Unknown request')
            action, raw, digest, status, saved, after = row
            if action != 'local_draft' or status == 'SUCCESS':
                return self._recorded(db,rid,saved)
            try:
                params = json.loads(raw)
                if fingerprint(action, params) != digest:
                    raise DraftError('Stored binding changed')
                expected = expectation(rid, params)
            except (TypeError, ValueError, UnicodeError):
                return self.store(db, rid, self.response(rid, 'RECOVERY_BLOCKED',
                                  outcome_verified=False, error='Stored draft binding invalid; do not replay'))
            proof = {'method': 'independent_file_read', 'request_id': rid, 'input_digest': digest,
                     'expected_sha256': expected.sha256, 'expected_bytes': len(expected.data),
                     'observed_sha256': None, 'observed_bytes': None}
            try:
                proof.update(self.local_drafts.observe(rid, expected))
                matches = proof['observed_sha256'] == expected.sha256 and proof['observed_bytes'] == len(expected.data)
                proof['status'] = 'matched' if matches else 'mismatch'
                outcome = 'SUCCESS' if matches else 'OUTCOME_MISMATCH'
            except (OSError, DraftError) as exc:
                matches, outcome = False, 'VERIFICATION_UNAVAILABLE'
                proof.update(status='unavailable', reason=type(exc).__name__)
            proof['observed_at'] = self.clock()
            # A missing file during a current write is not evidence of failure.
            if not matches and status == 'IN_PROGRESS' and after is not None and after > self.clock():
                return json.loads(saved)
            result = self.response(rid, outcome, verified=matches, outcome_verified=matches,
                                   action_verified=False, recovered_by_observation=True,
                                   outcome_evidence=proof, result={'path': str(self.local_drafts.path(rid, expected)),
                                   'publication': None, 'write_error': None, 'delivered': False, 'replayed': False},
                                   error=None if matches else 'Observation incomplete; do not replay')
            return self.store(db, rid, result)

    def recover_pending(self):
        with self.connect() as db:
            ids = [r[0] for r in db.execute("SELECT id FROM requests WHERE action='local_draft' AND status='IN_PROGRESS'")]
        results = [self.reconcile(rid) for rid in ids]
        with self.connect() as db:
            plans = [r[0] for r in db.execute("SELECT id FROM requests WHERE action='local_draft_plan' AND status NOT IN ('SUCCESS','CANCELLED') ORDER BY created_at,id")]
        from pablo_work_plans import WorkPlans
        return results + [WorkPlans(self).advance(rid) for rid in plans]

    def advance_plan(self, rid):
        with self.connect() as db:
            row = db.execute('SELECT action FROM requests WHERE id=?', (rid,)).fetchone()
        if not row or row[0] != 'local_draft_plan':
            return self.response(rid, 'NOT_FOUND', error='Unknown draft plan')
        from pablo_work_plans import WorkPlans
        return WorkPlans(self).advance(rid)

    def cancel_plan(self, rid):
        from pablo_work_plans import WorkPlans
        try:
            return WorkPlans(self).cancel(rid)
        except (DraftError, TypeError, ValueError):
            return self.response(rid, 'RECOVERY_BLOCKED', error='Invalid or unknown plan')

    def get(self, rid):
        with self.connect() as db:
            row = db.execute('SELECT response FROM requests WHERE id=?', (rid,)).fetchone()
            return self._recorded(db,rid,row[0]) if row else self.response(rid, 'NOT_FOUND', error='Unknown request')

    def approval_snapshot(self):
        """No messages or params are exposed; expired approvals need renewal."""
        with self.connect() as db:
            from pablo_approval_maintenance import journal_decay
            journal_decay(db,self.clock())
            waiting, expired = db.execute(
                "SELECT coalesce(sum(expires>=?),0), coalesce(sum(expires<?),0) FROM requests "
                "WHERE status='APPROVAL_REQUIRED' AND consumed=0", (self.clock(), self.clock())).fetchone()
            expired=db.execute("SELECT count(*) FROM approval_archives WHERE source='journal' AND reason='EXPIRED'").fetchone()[0]
            legacy_expired=db.execute("SELECT count(*) FROM approval_archives a JOIN requests r ON r.id=a.source_id WHERE a.source='journal' AND a.reason='EXPIRED' AND r.created_at IS NULL").fetchone()[0]
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            unknown=db.execute("SELECT count(*) FROM approval_notifications WHERE status IN ('delivery_unknown','sending')").fetchone()[0] if 'approval_notifications' in tables else 0
        return {'journal_waiting': waiting, 'journal_expired': expired, 'journal_legacy_expired':legacy_expired, 'journal_complete': True,'notification_delivery_unknown':unknown}

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

    def execute(self, action, params, request_id=None, parent_id=None):
        rid = request_id or str(uuid.uuid4())
        if not isinstance(rid, str) or not rid or len(rid) > 128 or not isinstance(params, dict):
            return self.response(str(rid)[:128], 'ERROR', error='Invalid request')
        params = json.loads(json.dumps(params))
        if action == 'local_draft':
            try:
                expectation(rid, params)
            except (DraftError, TypeError, UnicodeError):
                return self.response(rid, 'ERROR', error='Invalid local draft contract', outcome_verified=False)
        if action == 'local_draft_plan':
            from pablo_work_plans import validate_plan
            try:
                validate_plan(rid, params)
            except (DraftError, TypeError, UnicodeError):
                return self.response(rid, 'ERROR', error='Invalid local draft plan', outcome_verified=False)
        if action in ANTIGRAVITY_ALIASES:
            action='antigravity'
            try:
                params=prepare_antigravity(params)
            except Exception as exc:
                return self.response(rid,'BLOCKED',error=type(exc).__name__)
        digest = fingerprint(action, params)
        with self.lock, self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT digest,response FROM requests WHERE id=?', (rid,)).fetchone()
            if row:
                if row[0] != digest:
                    return self.response(rid, 'CONFLICT', error='Request ID reused with changed action/params')
                return self._recorded(db,rid,row[1])
            if parent_id is not None:
                from pablo_work_plans import validate_plan, step_id, step_params
                parent = db.execute("SELECT params,digest,status FROM requests WHERE id=? AND action='local_draft_plan'", (parent_id,)).fetchone()
                try:
                    plan = validate_plan(parent_id, json.loads(parent[0])) if parent else None
                    bound = bool(action == 'local_draft' and plan and parent[2] != 'CANCELLED' and fingerprint('local_draft_plan', plan) == parent[1]
                                 and any(step_id(parent_id, s['name']) == rid and fingerprint('local_draft', step_params(parent_id, plan, s)) == digest for s in plan['steps']))
                except (ValueError, TypeError, UnicodeError):
                    bound = False
                if not bound:
                    return self.response(rid, 'CONFLICT', error='Invalid parent step binding')
            result = self.response(rid, 'IN_PROGRESS')
            db.execute('INSERT INTO requests(id,digest,action,params,status,response) VALUES(?,?,?,?,?,?)',
                       (rid, digest, action, json.dumps(params), result['status'], json.dumps(result)))
            db.execute('UPDATE requests SET created_at=? WHERE id=?',(self.clock(),rid))
            db.execute('UPDATE requests SET parent_id=? WHERE id=?', (parent_id, rid))
            self._phase(db, rid, 'claimed')
            if action in ('local_draft', 'local_draft_plan'):
                db.execute('UPDATE requests SET deadline_at=?,observation_after=? WHERE id=?',
                           (params.get('deadline_at'), self.clock() + 300, rid))
            # Kırmızı Çizgi Kontrolü (Approval Gate)
            needs_approval, reason = is_approval_required(action, params)
            if needs_approval:
                aid = str(uuid.uuid4())
                if self.approvals is not None:
                    try:
                        record=self.approvals.request('journal',rid,action_binding(rid,action,params,digest),
                                                      self.clock()+self.ttl,self.clock())
                        aid=record['approval_id']
                        if record['status']!='pending':
                            return self.store(db,rid,self.response(rid,'BLOCKED',error='Canonical request is not pending; do not replay'))
                    except ApprovalUnavailable:
                        return self.store(db,rid,self.response(rid,'APPROVAL_UNAVAILABLE',error='Canonical approval unavailable; no local grant'))
                result = self.response(rid, 'APPROVAL_REQUIRED', approval_id=aid, reason=reason, error=f'Owner approval required: {reason}')
                db.execute('UPDATE requests SET approval=?,expires=? WHERE id=?', (aid, self.clock() + self.ttl, rid))
                return self.store(db, rid, result)

            if action not in self.actions and action not in ('local_draft', 'local_draft_plan'):
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
            if self.clock() >= expires or fingerprint(action, params) != digest:
                db.execute('UPDATE requests SET consumed=1 WHERE id=?', (rid,))
                return self.store(db, rid, self.response(rid, 'REJECTED', error='Expired, changed or rejected approval'))
            if self.approvals is not None:
                try:
                    binding=action_binding(rid,action,params,digest)
                    self.approvals.decide(approval_id,binding,user_id,chat_id,not reject)
                    if not reject:
                        claim=self.approvals.claim(approval_id,binding,'pablo')
                        db.execute('UPDATE requests SET canonical_claim=? WHERE id=?',(claim['claim_id'],rid))
                except ApprovalUnavailable:
                    return self.response(rid,'APPROVAL_UNAVAILABLE',error='Decision or claim unavailable; no execution')
            if reject:
                db.execute('UPDATE requests SET consumed=1 WHERE id=?',(rid,))
                return self.store(db,rid,self.response(rid,'REJECTED',error='Owner rejected approval'))
            db.execute('UPDATE requests SET consumed=1 WHERE id=?', (rid,))
            self.store(db, rid, self.response(rid, 'IN_PROGRESS'))
            db.commit()
        result=self._run(rid, action, params)
        if self.approvals is not None:
            with self.connect() as db:
                row=db.execute('SELECT canonical_claim FROM requests WHERE id=?',(rid,)).fetchone()
            if row and row[0]:
                try: self.approvals.complete(approval_id,row[0],'pablo',result['status'])
                except ApprovalUnavailable: result['approval_reconciliation']='required'
        return result

    def _run_local_draft(self, rid, params):
        with self.lock:
            with self.connect() as db:
                saved = db.execute('SELECT status,response FROM requests WHERE id=?', (rid,)).fetchone()
                if saved and saved[0] == 'SUCCESS':
                    return json.loads(saved[1])
                self._phase(db, rid, 'publishing')
            expected = expectation(rid, params)
            proof = {'method': 'independent_file_read', 'request_id': rid,
                     'input_digest': fingerprint('local_draft', params),
                     'expected_sha256': expected.sha256, 'expected_bytes': len(expected.data),
                     'observed_sha256': None, 'observed_bytes': None, 'observed_at': self.clock()}
            publication, write_error = None, None
            try:
                publication = self.local_drafts.write(rid, expected)
            except (OSError, DraftError) as exc:
                write_error = type(exc).__name__
            with self.connect() as db:
                self._phase(db, rid, 'observing')
            try:
                proof.update(self.local_drafts.observe(rid, expected))
                matches = (proof['observed_sha256'] == expected.sha256
                           and proof['observed_bytes'] == len(expected.data))
                status = 'SUCCESS' if matches else 'OUTCOME_MISMATCH'
                proof['status'] = 'matched' if matches else 'mismatch'
            except (OSError, DraftError) as exc:
                matches, status = False, 'VERIFICATION_UNAVAILABLE'
                proof.update(status='unavailable', reason=type(exc).__name__)
            proof['observed_at'] = self.clock()
            result = self.response(rid, status, verified=matches, outcome_verified=matches,
                                   action_verified=write_error is None,
                                   outcome_evidence=proof,
                                   result={'path': str(self.local_drafts.path(rid, expected)),
                                           'publication': publication, 'write_error': write_error,
                                           'delivered': False},
                                   error=None if matches else 'Local draft outcome did not verify')
            with self.connect() as db:
                return self.store(db, rid, result)

    def _run(self, rid, action, params):
        if action == 'local_draft_plan':
            from pablo_work_plans import WorkPlans
            return WorkPlans(self).advance(rid)
        if action == 'local_draft':
            return self._run_local_draft(rid, params)
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
                    status=raw.get('status') if action=='antigravity' else None
                    result = self.response(rid, status or ('SUCCESS' if ok else 'ERROR'), result=raw.get('result'),
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
