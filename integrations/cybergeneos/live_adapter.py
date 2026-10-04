"""Owner-only native audio transport; the existing Jeff remains answer authority.

Tokens lock the voice model, instructions and tool. Consultations are journalled
before execution: interrupted/unknown calls are never automatically executed again.
"""
from contextlib import closing
import datetime
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
import time
import urllib.request

MODEL = 'models/gemini-3.8-live'
TOKEN_URL = 'https://generativelanguage.googleapis.com/v1beta/auth_tokens'
WS_URL = ('wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.'
          'v1beta.GenerativeService.BidiGenerateContentConstrained')
VOICE_RULES = (
    "Sen gerçek Jeff'in canlı ses arayüzüsün. Türkçe, doğal, kısa konuş. "
    "Her kullanıcı ifadesi için önce consult_jeff çağır; text tam kullanıcının isteği olsun, "
    "isteğine eylem, onay veya bilgi ekleme. Araç yanıtı gelmeden ses üretme. "
    "Yalnız aracın answer alanını aynen seslendir; sayıları, belirsizliği ve olumsuzlukları değiştirme. "
    "Kendinden hafıza, tamamlanma, durum, yetki veya başarı ekleme. "
    "Kullanıcı araya girerse sus ve onu dinle. Görüşmeyi başlatınca kendiliğinden konuşma. "
    "Araç hata verirse yalnız gerçek Jeff'e ulaşılamadığını söyle; alternatif cevap uydurma."
)


def setup(voice='Charon'):
    if voice not in {'Charon', 'Orus', 'Algieba', 'Sadaltager'}:
        voice = 'Charon'
    return {
        'model': MODEL,
        'generationConfig': {'responseModalities': ['AUDIO'],
                             'speechConfig': {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': voice}}}},
        'systemInstruction': {'parts': [{'text': VOICE_RULES}]},
        'tools': [{'functionDeclarations': [{'name': 'consult_jeff',
                   'description': 'Kullanıcının isteğini gerçek Jeff ile değerlendir; cevabını al.',
                   'parameters': {'type': 'OBJECT', 'properties': {'text': {'type': 'STRING'}},
                                  'required': ['text']}}]}],
        'inputAudioTranscription': {}, 'outputAudioTranscription': {},
        'realtimeInputConfig': {'activityHandling': 'START_OF_ACTIVITY_INTERRUPTS',
                               'automaticActivityDetection': {'silenceDurationMs': 600,
                                                               'prefixPaddingMs': 120}},
        'sessionResumption': {}, 'contextWindowCompression': {'slidingWindow': {}}}


class Refused(Exception):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason


class LiveCalls:
    def __init__(self, path, key_reader, reply, clock=time.time, token_request=None):
        self.path = Path(path)
        self.key_reader, self.reply, self.clock = key_reader, reply, clock
        self.token_request = token_request or self._token
        self.lock = threading.Lock()
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS voice_sessions (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS voice_calls (
                    session TEXT NOT NULL, id TEXT NOT NULL, binding TEXT NOT NULL,
                    state TEXT NOT NULL, answer TEXT,
                    PRIMARY KEY(session,id));
            ''')
        self.path.chmod(0o600)

    def db(self):
        # closing is required: sqlite context manager does not close the handle.
        return closing(sqlite3.connect(self.path, timeout=3, isolation_level=None))

    def _token(self, body):
        key = self.key_reader()
        if not key:
            raise Refused(503, 'ses_anahtari_yok')
        request = urllib.request.Request(TOKEN_URL, data=json.dumps(body).encode(),
                    headers={'x-goog-api-key': key, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=20) as response:
            name = json.load(response).get('name')
        if not isinstance(name, str) or not name.startswith('auth_tokens/'):
            raise Refused(502, 'ses_baglantisi_kurulamadi')
        return name

    def session(self, owner, voice):
        now = self.clock()
        with self.db() as db:
            if db.execute('SELECT count(*) FROM voice_sessions WHERE owner=? AND expires>?',
                          (owner, now)).fetchone()[0] >= 4:
                raise Refused(429, 'cok_fazla_gorusme')
        config = setup(voice)
        stamp = lambda seconds: datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
        token = self.token_request({'uses': 1, 'expireTime': stamp(now + 1200),
                                   'newSessionExpireTime': stamp(now + 60),
                                   'bidiGenerateContentSetup': config})
        nonce = secrets.token_urlsafe(32)
        sid = hashlib.sha256(nonce.encode()).hexdigest()
        with self.db() as db:
            db.execute('INSERT INTO voice_sessions VALUES(?,?,?)', (sid, owner, now + 1200))
        return {'token': token, 'session': nonce, 'setup': config, 'websocket': WS_URL,
                'expires_at': now + 1200, 'answer_authority': 'real_jeff'}

    def consult(self, owner, body):
        nonce, cid, text = (body.get(k) for k in ('session', 'call_id', 'text'))
        if (not isinstance(nonce, str) or len(nonce) > 100 or not isinstance(cid, str)
                or not 1 <= len(cid) <= 160 or not isinstance(text, str)
                or not 1 <= len(text.strip()) <= 1200):
            raise Refused(400, 'gecersiz_konusma')
        text = text.strip()
        sid = hashlib.sha256(nonce.encode()).hexdigest()
        binding = hashlib.sha256(text.encode()).hexdigest()
        with self.db() as db:
            row = db.execute('SELECT owner,expires FROM voice_sessions WHERE id=?', (sid,)).fetchone()
            if not row or row[0] != owner or row[1] <= self.clock():
                raise Refused(403, 'gorusme_suresi_doldu')
            prior = db.execute('SELECT binding,state,answer FROM voice_calls WHERE session=? AND id=?', (sid,cid)).fetchone()
            if prior:
                if prior[0] != binding:
                    raise Refused(409, 'konusma_kimligi_degisti')
                if prior[1] == 'ANSWERED':
                    return {'answer': prior[2], 'authority': 'real_jeff', 'cached': True}
                raise Refused(409, 'onceki_konusmanin_sonucu_bilinmiyor')
            if db.execute('SELECT count(*) FROM voice_calls WHERE session=?', (sid,)).fetchone()[0] >= 120:
                raise Refused(429, 'gorusme_siniri')
        if not self.lock.acquire(blocking=False):
            raise Refused(409, 'jeff_halen_dusunuyor')
        try:
            with self.db() as db:
                # The global consultation lock serialises admission and rechecks identity.
                if db.execute('SELECT 1 FROM voice_calls WHERE session=? AND id=?', (sid,cid)).fetchone():
                    raise Refused(409, 'onceki_konusmanin_sonucu_bilinmiyor')
                db.execute('INSERT INTO voice_calls VALUES(?,?,?, ?,NULL)', (sid,cid,binding,'RUNNING'))
            try:
                answer = ''.join(self.reply(text))
                if not answer.strip():
                    raise RuntimeError('empty_reply')
            except Exception:
                with self.db() as db:
                    db.execute("UPDATE voice_calls SET state='OUTCOME_UNKNOWN' WHERE session=? AND id=?", (sid,cid))
                raise Refused(502, 'jeff_yaniti_dogrulanamadi') from None
            with self.db() as db:
                db.execute("UPDATE voice_calls SET state='ANSWERED',answer=? WHERE session=? AND id=?", (answer,sid,cid))
            return {'answer': answer, 'authority': 'real_jeff', 'cached': False}
        finally:
            self.lock.release()

    def end(self, owner, nonce):
        if not isinstance(nonce,str) or len(nonce)>100:
            raise Refused(400,'gecersiz_gorusme')
        with self.db() as db:
            db.execute('UPDATE voice_sessions SET expires=? WHERE id=? AND owner=?',
                       (self.clock(),hashlib.sha256(nonce.encode()).hexdigest(),owner))
        return {'ok': True}


def patch_app(source):
    anchor = '    install_jarvis_adapter(sys.modules[__name__])\n'
    addition = '    from .live_adapter import install as install_live_adapter\n    install_live_adapter(sys.modules[__name__])\n'
    if addition in source:
        return source
    if source.count(anchor) != 1:
        raise ValueError('Panel install anchor changed')
    return source.replace(anchor,anchor+addition)


def install(app):
    if getattr(app, '_live_installed', False):
        return
    calls = LiveCalls(Path(app.DATA)/'voice-calls.sqlite3', lambda:app.llm._key,
                      lambda text: app.jeff.stream_reply(text, app.briefing.jeff_context(app.store)))
    original = app.H.route
    def route(handler, parts, body):
        if parts[:2] != ['api','voice']:
            return original(handler,parts,body)
        if handler.by != 'bilal' or not handler._authed():
            return 403, {'error': 'sahip_gerekiyor'}
        # Same-origin browser request; Jeff's bearer token never grants voice access.
        from urllib.parse import urlparse
        origin = handler.headers.get('Origin')
        if not origin or urlparse(origin).hostname not in app.ALLOWED:
            return 403, {'error': 'kaynak'}
        from http.cookies import SimpleCookie
        cookies = SimpleCookie(handler.headers.get('Cookie',''))
        if 'cgos' not in cookies:
            return 403, {'error': 'sahip_gerekiyor'}
        owner = hashlib.sha256(cookies['cgos'].value.encode()).hexdigest()
        try:
            if parts == ['api','voice','end']:
                return 200, calls.end(owner,body.get('session'))
            if app.jeff.mode() != 'hermes':
                raise Refused(503, 'gercek_jeff_bagli_degil')
            if parts == ['api','voice','session']:
                if app.llm_limited(handler._ip()):
                    raise Refused(429, 'cok_sik')
                return 200, calls.session(owner,body.get('voice'))
            if parts == ['api','voice','consult']:
                return 200, calls.consult(owner,body)
            return 404, {'error': 'yok'}
        except Refused as e:
            return e.status, {'error': e.reason}
        except Exception:
            return 502, {'error': 'ses_baglantisi_kurulamadi'}
    app.H.route = route
    app._live_installed = True
