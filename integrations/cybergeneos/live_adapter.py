"""Owner-only native audio transport; the existing Jeff remains answer authority.

Tokens lock the voice model, instructions and tool. Consultations are journalled
before execution: interrupted/unknown calls are never automatically executed again.
"""
from contextlib import closing
import datetime
import hashlib
import json
import os
import re
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
FAST_DIALOGUE = (
    'merhaba', 'merhaba jeff', 'selam', 'selam jeff', 'günaydın', 'iyi akşamlar',
    'nasılsın', 'nasılsın jeff', 'beni duyuyor musun', 'jeff beni duyuyor musun',
    'orada mısın', 'jeff orada mısın', 'teşekkürler', 'teşekkür ederim',
    'tamam', 'peki', 'bir fikrim var', 'birlikte düşünelim', 'çok yoruldum',
    'konuşalım', 'dur beni dinle')
VOICE_RULES = (
    "Sen gerçek Jeff'in canlı ses arayüzüsün. Türkçe, doğal, kısa konuş. "
    "Yalnız şu kısa konuşma ifadelerine doğrudan cevap verebilirsin: " + ', '.join(FAST_DIALOGUE) + '. '
    "Bunlarda en fazla bir kısa cümleyle selam ver, dinlediğini söyle veya empati kur. "
    "Hiçbir güncel durum, kişisel hafıza, iş sonucu, eylem veya onay iddiası ekleme. "
    "Diğer her kullanıcı ifadesi için önce consult_jeff çağır; text tam kullanıcının isteği olsun, "
    "isteğine eylem, onay veya bilgi ekleme. Araç yanıtı gelmeden ses üretme. "
    "Araç cevap parçaları gönderir. Her yeni answer parçasını yalnız bir kez aynen seslendir; "
    "eski parçayı tekrarlama. Sayıları, belirsizliği ve olumsuzlukları değiştirme. "
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
                   'description': 'Kullanıcının isteğini gerçek Jeff ile değerlendir; cevabını parçalar halinde al.',
                   'behavior': 'NON_BLOCKING',
                   'parameters': {'type': 'OBJECT', 'properties': {'text': {'type': 'STRING'}},
                                  'required': ['text']}}]}],
        'inputAudioTranscription': {}, 'outputAudioTranscription': {},
        'realtimeInputConfig': {'activityHandling': 'START_OF_ACTIVITY_INTERRUPTS',
                               'automaticActivityDetection': {'silenceDurationMs': 350,
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
                'expires_at': now + 1200, 'answer_authority': 'real_jeff',
                'fast_dialogue_phrases': list(FAST_DIALOGUE), 'conversation_engine': 'native_live'}

    def consult(self, owner, body):
        result = None
        for event in self.consult_stream(owner, body):
            if event['t'] == 'end':
                result = {k: v for k, v in event.items() if k != 't'}
        return result

    def consult_stream(self, owner, body):
        """Yield real Jeff sentences; partial words never imply completed execution."""
        started = time.monotonic()
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
                    yield {'t': 'end', 'answer': prior[2], 'authority': 'real_jeff', 'cached': True}
                    return
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
                yield {'t': 'accepted', 'authority': 'real_jeff', 'completion_verified': False}
                pieces = []
                pending = ''
                first = None
                for piece in self.reply(text):
                    if not isinstance(piece, str):
                        raise RuntimeError('invalid_reply')
                    pieces.append(piece)
                    pending += piece
                    # Complete sentences only: never split a number at its decimal point.
                    while (match := re.search(r'[.!?]\s+', pending)):
                        end = match.end()
                        chunk, pending = pending[:end], pending[end:]
                        if chunk.strip():
                            if first is None: first = time.monotonic() - started
                            yield {'t': 'piece', 'answer': chunk, 'authority': 'real_jeff', 'completion_verified': False}
                answer = ''.join(pieces)
                if not answer.strip():
                    raise RuntimeError('empty_reply')
                if pending.strip():
                    if first is None: first = time.monotonic() - started
                    yield {'t': 'piece', 'answer': pending, 'authority': 'real_jeff', 'completion_verified': False}
            except BaseException as exc:
                with self.db() as db:
                    db.execute("UPDATE voice_calls SET state='OUTCOME_UNKNOWN' WHERE session=? AND id=?", (sid,cid))
                if isinstance(exc, (GeneratorExit, KeyboardInterrupt, SystemExit)): raise
                raise Refused(502, 'jeff_yaniti_dogrulanamadi') from None
            with self.db() as db:
                db.execute("UPDATE voice_calls SET state='ANSWERED',answer=? WHERE session=? AND id=?", (answer,sid,cid))
            yield {'t': 'end', 'answer': answer, 'authority': 'real_jeff', 'cached': False,
                   'first_sentence_seconds': first, 'answer_seconds': time.monotonic() - started}
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
    def reply(text):
        from .jarvis_adapter import STATUS_REQUESTS
        # Voice punctuation does not change an exact infrastructure status request.
        clean=text.strip().rstrip('.!?').casefold()
        if clean in STATUS_REQUESTS:
            # The shared deterministic reader ignores panel business context entirely.
            return app.jeff.stream_reply(clean, '')
        # Voice starts with current infrastructure truth. Jeff can consult his existing
        # tools for other subjects; no business query or workflow is modified here.
        # Avoid a Windows round trip before every conversational turn. No stale
        # status is injected: Jeff must consult existing tools when facts are needed.
        return app.jeff.stream_reply(text, json.dumps({'live_voice': True,
            'status_not_prefetched': True,
            'rule': 'Güncel durum bu mesajda okunmadı. Durum gerekiyorsa mevcut araçlarla doğrula; tahmin etme.'},ensure_ascii=False))
    calls = LiveCalls(Path(app.DATA)/'voice-calls.sqlite3', lambda:app.llm._key, reply)
    original = app.H.route
    json_original = app.H._json
    class VoiceStream:
        def __init__(self, first, iterator):
            self.first, self.iterator = first, iterator
    def send_json(handler, code, out):
        if not isinstance(out, VoiceStream):
            return json_original(handler, code, out)
        try:
            handler._stream_headers('application/x-ndjson')
            def emit(event):
                handler.wfile.write((json.dumps(event,ensure_ascii=False)+'\n').encode())
                handler.wfile.flush()
            emit(out.first)
            for event in out.iterator: emit(event)
        except Refused as exc:
            try: emit({'t':'err','error':exc.reason})
            except OSError: pass
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            out.iterator.close()  # Partial answer on a disconnected client stays unknown.
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
                if body.get('stream') is True:
                    iterator=calls.consult_stream(owner,body)
                    return 200, VoiceStream(next(iterator),iterator)
                return 200, calls.consult(owner,body)
            return 404, {'error': 'yok'}
        except Refused as e:
            return e.status, {'error': e.reason}
        except Exception:
            return 502, {'error': 'ses_baglantisi_kurulamadi'}
    app.H.route = route
    app.H._json = send_json
    app._live_installed = True
