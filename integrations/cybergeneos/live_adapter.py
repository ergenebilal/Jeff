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
PROOF_REQUIRED = (r'(?i)(onay|görev|pablo|durum|bitir|bitti|tamamla|tamamlandı|yaptın|yapıldı|'
    r'başlat|çalıştır|gönder|kaydet|arşiv|iptal|hatır|hafıza|müşteri|lead|radar|'
    r'para|fiyat|hesap|ödeme|bakiye|sermaye|bugün|şimdi|güncel|haber|hava|'
    r'takvim|randevu|sil(?:me|in|indi)?\b|dosya|sunucu|\biş(?:ler|leri|im|in)?\b)')
RECORD_SUMMARIES = {
    'bugün ne var', 'bugün ne var jeff', 'jeff bugün ne var',
    'bekleyen iş var mı', 'işler ne durumda',
    'onay bekleyen var mı', 'bekleyen onay var mı',
}
VOICE_RULES = (
    "Sen Bilal'in Jeff adlı asistanının canlı konuşma katmanısın. Türkçe, doğal, kısa konuş. "
    "Sıradan sohbeti, genel açıklamaları, fikirleri birlikte düşünmeyi ve empatiyi DOĞRUDAN canlı yanıtla; "
    "her cümleyi başka modele danışıp kullanıcıyı bekletme. Varsayımını gerçek diye sunma. "
    "ÖNEMLİ: Ses/bağlantı denemesinde bile 'deneme başarılı', 'her şey yolunda', 'ses net', "
    "'sistem çalışıyor' gibi ölçmediğin kalite veya başarı iddiaları üretme. "
    "Bir ses denemesinde yalnız 'Bu bir ses denemesi. Söylediklerinizi aldım. "
    "Cihazınızdaki ses kalitesini buradan doğrulayamam.' diyebilirsin. "
    "Kullanıcının kişisel hafızası, güncel panel/iş/onay/para durumu, haber veya bir işlemin yapılması "
    "gerekiyorsa MUTLAKA consult_jeff çağır. Verilmeyen geçmişi veya mevcut durumu uydurma. "
    "Yalnız gerçek araç sonucuna dayanarak iş, onay veya başarı hakkında konuş. "
    "consult_jeff içindeki text tam kullanıcının isteği olsun, "
    "isteğine eylem, onay veya bilgi ekleme. Kayıt/iş cevabı için araç yanıtını bekle. "
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
                   'description': 'Güncel kayıt, kişisel hafıza veya işlem gereken isteği gerçek Jeff ile değerlendir; sıradan sohbet için kullanma.',
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


def guarded_reply(pieces, current, renderer):
    """No overall-health evidence is supplied by this transport. Block observed
    unsupported health/empty-work claims before their sentence reaches audio.
    This is a limited guard, not a universal semantic proof of every answer.
    """
    def unsupported(sentence):
        text=sentence.casefold()
        if re.search(r'(sistem\s+sağlıklı|her\s+şey\s+yolunda|hepsi\s+zamanında|acil\s+iş\s+yok)',text):return True
        work=current.get('work',{})
        if re.search(r'bekleyen\s+(?:görev|iş)(?:\s+veya\s+acil\s+iş)?\s+yok',text):
            return not work.get('known') or work.get('open',0)>0
        approvals=current.get('approvals',{})
        if re.search(r'(?:bekleyen\s+)?onay\s+yok',text):
            return not approvals.get('known') or approvals.get('pending',0)>0
        return False
    pending=''
    try:
        for piece in pieces:
            pending+=piece
            while (match:=re.search(r'[.!?]\s+',pending)):
                sentence,pending=pending[:match.end()],pending[match.end():]
                if unsupported(sentence):
                    yield 'Bu yanıtın genel sağlık veya boş iş iddiası doğrulanmadı. '+renderer(current)
                    return
                yield sentence
        if pending:
            if unsupported(pending):yield 'Bu yanıtın genel sağlık veya boş iş iddiası doğrulanmadı. '+renderer(current)
            else:yield pending
    finally:
        close=getattr(pieces,'close',None)
        if close:close()


class LiveCalls:
    def __init__(self, path, key_reader, reply, clock=time.time, token_request=None, context_reply=None):
        self.path = Path(path)
        self.key_reader, self.reply, self.clock = key_reader, reply, clock
        self.token_request = token_request or self._token
        self.context_reply = context_reply
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
                'fast_dialogue_phrases': list(FAST_DIALOGUE), 'conversation_engine': 'native_live',
                'native_conversation': True, 'proof_required_pattern': PROOF_REQUIRED[4:]}

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
        dialogue = body.get('dialogue', [])
        if (not isinstance(dialogue,list) or len(dialogue)>12 or
                any(not isinstance(m,dict) or m.get('role') not in {'user','assistant'} or
                    not isinstance(m.get('content'),str) or len(m['content'])>1200 for m in dialogue) or
                sum(len(m['content']) for m in dialogue)>6000):
            raise Refused(400,'gecersiz_konusma_baglami')
        dialogue=[{'role':m['role'],'content':m['content']} for m in dialogue]
        sid = hashlib.sha256(nonce.encode()).hexdigest()
        bound=json.dumps({'text':text,'dialogue':dialogue},sort_keys=True,ensure_ascii=False) if 'dialogue' in body else text
        binding = hashlib.sha256(bound.encode()).hexdigest()
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
                yield {'t': 'accepted', 'authority': 'real_jeff', 'completion_verified': False,
                       'progress': 'Kontrol ediyorum.'}
                pieces = []
                pending = ''
                first = None
                replies=self.context_reply(text,dialogue) if self.context_reply else self.reply(text)
                for piece in replies:
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
    def reply(text,dialogue=None):
        from .jarvis_adapter import STATUS_REQUESTS
        # Voice punctuation does not change an exact infrastructure status request.
        clean=text.strip().rstrip('.!?').casefold()
        if clean in STATUS_REQUESTS:
            # The shared deterministic reader ignores panel business context entirely.
            return app.jeff.stream_reply(clean, '')
        if clean in RECORD_SUMMARIES:
            from scripts.jarvis_snapshot import render
            answer='İş ve onay kayıtlarında: '+render(app._jarvis_snapshot())
            if 'bugün' in clean:
                answer+=' Bugünün takvimini ve genel sistem sağlığını bu yanıtla doğrulamadım.'
            return iter([answer])
        # Voice starts with current infrastructure truth. Jeff can consult his existing
        # tools for other subjects; no business query or workflow is modified here.
        # Ordinary conversation is already native. A grounded consultation can
        # wait for current records while truthful progress is spoken in parallel.
        current=app._jarvis_snapshot()
        from scripts.jarvis_snapshot import render
        pieces=app.jeff.stream_reply(text, json.dumps({'live_voice': True,
            'jarvis_snapshot':current,
            'voice_dialogue': dialogue or [],
            'rule': 'Bu güncel kayıtla çelişme. Açık iş veya kanıtsız sonuç varken işleri boş veya sistemi sağlıklı sayma. Genel sağlık kanıtı bu mesajda yok.'},ensure_ascii=False))
        return guarded_reply(pieces,current,render)
    calls = LiveCalls(Path(app.DATA)/'voice-calls.sqlite3', lambda:app.llm._key, reply, context_reply=reply)
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
