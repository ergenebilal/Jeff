"""Persistent company -> official-source research -> draft -> owner review.

No delivery action is called here. A completion proves a saved, source-checked
draft, not the company's actual need or the truth of its own website claims.
"""
import hashlib
import json
import os
import re
import time
import uuid

from . import analysis, contact, outreach
from .store import now

SCHEMA = """
CREATE TABLE IF NOT EXISTS marketing_runs(
 job_id TEXT PRIMARY KEY, lead_id TEXT NOT NULL, input_json TEXT NOT NULL,
 input_digest TEXT NOT NULL, checkpoint TEXT NOT NULL DEFAULT '{}', published_at INTEGER);
CREATE TABLE IF NOT EXISTS marketing_requests(
 request_key TEXT PRIMARY KEY, job_id TEXT NOT NULL, lead_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS marketing_reviews(
 id TEXT PRIMARY KEY, job_id TEXT NOT NULL, digest TEXT NOT NULL, decision TEXT NOT NULL,
 actor TEXT NOT NULL, text TEXT NOT NULL, created_at INTEGER NOT NULL);
"""
INPUT_FIELDS = ('name', 'website', 'city', 'district', 'sector', 'category',
                'gate', 'gate_override', 'gate_info', 'ref', 'stage', 'contacts',
                'analysis', 'analysis_at', 'drafts', 'draft')


class Conflict(Exception):
    pass


def _json(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(data):
    return hashlib.sha256(_json(data).encode()).hexdigest()


def snapshot(lead):
    return {k: lead.get(k) for k in INPUT_FIELDS}


def init(store):
    with store.lock:
        store.db.executescript(SCHEMA)
        store.db.commit()


def _eligible(store, lead):
    if not lead:
        raise Conflict('Firma bulunamadı.')
    if contact.opted_out(store, lead['id']):
        raise Conflict('Firma ret listesinde; araştırma ve taslak başlatılmadı.')
    if lead['stage'] in ('Gönderildi', 'Yanıt geldi', 'Görüşme', 'Kazanıldı', 'Kapandı'):
        raise Conflict('Bu firma ilk temas aşamasını geçti; mevcut çalışma korunuyor.')
    if lead.get('gate') != 'geçti' and not lead.get('gate_override'):
        raise Conflict('Önce firmanın ön kontrolünü tamamlayın.')
    if not (lead.get('website') or '').startswith(('https://', 'http://')):
        raise Conflict('Araştırma için firmanın resmî web sitesini ekleyin.')


def start(store, lid, request_key, by='bilal'):
    """Atomically reuse the same request or active run, including after HTTP retries."""
    if not re.fullmatch(r'[A-Za-z0-9_-]{8,80}', str(request_key or '')):
        raise Conflict('Geçerli bir istek kimliği gerekli.')
    with store.lock, store.db:
        old = store.one('SELECT * FROM marketing_requests WHERE request_key=?', (request_key,))
        if old:
            if old['lead_id'] != lid:
                raise Conflict('Bu istek kimliği başka bir firmaya ait.')
            return old['job_id'], False
        lead = store.lead(lid)
        _eligible(store, lead)
        active = store.one("SELECT r.job_id FROM marketing_runs r JOIN jobs j ON j.id=r.job_id "
                           "WHERE r.lead_id=? AND j.status IN ('queued','running')", (lid,))
        if active:
            jid, created = active['job_id'], False
        else:
            cap = max(1, int(os.environ.get('CGOS_MARKETING_DAILY_CAP', '5')))
            count = store.one("SELECT count(*) n FROM jobs WHERE kind='marketing' AND created_at>=?", (now() - 86400,))['n']
            if count >= cap:
                raise Conflict(f'İlk kullanım sınırı: son 24 saatte {cap} firma. Sonuçları değerlendirdikten sonra devam edin.')
            # Do not compete with a separate gate/analysis that may update this record.
            for job in store.q("SELECT params FROM jobs WHERE kind IN ('analysis','gate') AND status IN ('queued','running')"):
                ids = json.loads(job['params']).get('ids') or []
                if not ids or lid in ids:
                    raise Conflict('Firma için başka bir inceleme sürüyor; bitmesini bekleyin.')
            if not lead.get('ref'):
                lead['ref'] = outreach.new_ref()
                store.db.execute('UPDATE leads SET ref=? WHERE id=?', (lead['ref'], lid))
            data = snapshot(lead)
            jid, created = 'j' + uuid.uuid4().hex[:10], True
            store.db.execute("INSERT INTO jobs(id,kind,title,params,status,progress,note,log,result,created_by,created_at) "
                             "VALUES(?,'marketing',?,?,'queued',0,'Sırada bekliyor','[]','{}',?,?)",
                             (jid, 'İnceleme ve taslak: ' + lead['name'][:60], _json({'ids': [lid]}), by, now()))
            store.db.execute('INSERT INTO marketing_runs(job_id,lead_id,input_json,input_digest) VALUES(?,?,?,?)',
                             (jid, lid, _json(data), digest(data)))
        store.db.execute('INSERT INTO marketing_requests VALUES(?,?,?)', (request_key, jid, lid))
        return jid, created


def _run(store, jid):
    r = store.one('SELECT * FROM marketing_runs WHERE job_id=?', (jid,))
    if not r:
        raise Conflict('Görevin kalıcı kaydı bulunamadı.')
    data = json.loads(r['input_json'])
    if digest(data) != r['input_digest']:
        raise Conflict('Görev girdisi değişmiş; çalışma durduruldu.')
    return r, data, json.loads(r['checkpoint'])


def _save(store, jid, checkpoint):
    store.x('UPDATE marketing_runs SET checkpoint=? WHERE job_id=?', (_json(checkpoint), jid))


def recover(store):
    """Resume completed checkpoints; an unrecorded model response needs explicit retry."""
    resumable = []
    for r in store.q("SELECT r.job_id,r.checkpoint FROM marketing_runs r JOIN jobs j ON j.id=r.job_id "
                     "WHERE j.status IN ('queued','running')"):
        try:
            cp = json.loads(r['checkpoint'])
            ambiguous = any(s.get('state') in ('calling', 'uncertain') for s in cp.values())
        except (ValueError, AttributeError, TypeError):
            ambiguous = True
        if ambiguous:
            store.update_job(r['job_id'], status='failed', finished_at=now(),
                             note='Yanıt kaydedilemeden kesildi; sonucu belirsiz. Yeniden başlatabilirsiniz.')
        else:
            store.update_job(r['job_id'], status='queued', note='Kayıtlı adımdan devam ediyor')
            resumable.append(r['job_id'])
    return resumable


def run(store, h, params):
    row, data, cp = _run(store, h.id)
    if row['published_at']:
        return 'İnceleme ve taslak daha önce kaydedildi.'
    if any(s.get('state') in ('calling', 'uncertain') for s in cp.values()):
        raise Conflict('Önceki yanıtın sonucu belirsiz; yeni çalışma açıkça başlatılmalı.')
    lead = {'id': row['lead_id'], **data}
    _eligible(store, store.lead(lead['id']))
    if digest(snapshot(store.lead(lead['id']))) != row['input_digest']:
        raise Conflict('Firma veya taslak değişti; mevcut kayıt korunuyor. Yeni inceleme başlatın.')
    for step, progress, note in (('research', 10, 'Jeff resmî kaynakları inceliyor'),
                                 ('draft', 65, 'Jeff bulgulara dayalı taslakları yazıyor')):
        if cp.get(step, {}).get('state') == 'done':
            continue
        if step == 'draft' and cp['research']['output']['karar'] != 'bulgu_var':
            break
        h.step(progress, note, log=note)
        analysis.check_ready()
        cp[step] = {'state': 'calling', 'started_at': now()}
        _save(store, h.id, cp)
        started = time.monotonic()
        receipt = {}
        try:
            if step == 'research':
                output = analysis.analyze(store, lead, persist=False, official_only=True,
                                          receipt=receipt, session=h.id + '-research')
                if output['karar'] == 'hata':
                    raise Conflict('Jeff geçerli bir araştırma sonucu üretemedi.')
            else:
                lead['analysis'] = _json(cp['research']['output'])
                output = contact.write_drafts(store, lead, persist=False, receipt=receipt, session=h.id + '-draft')
        except Exception:
            # A thrown/timeout response has no durable output. Never quietly repeat it.
            cp[step].update(state='uncertain', elapsed_seconds=round(time.monotonic() - started, 2))
            _save(store, h.id, cp)
            raise
        cp[step] = {'state': 'done', 'output': output, 'usage': receipt,
                    'elapsed_seconds': round(time.monotonic() - started, 2), 'finished_at': now()}
        _save(store, h.id, cp)
        h.step(progress + 20, 'Adım kaydedildi', log='Araştırma kaydedildi' if step == 'research' else 'Taslak kaydedildi')
    publish(store, h.id)
    no_draft = 'draft' not in cp
    h.step(100, 'Taslak üretilmedi: yeterli bulgu yok' if no_draft else 'Kaynaklı inceleme ve taslak değerlendirmenize hazır',
           result={'lead_id': lead['id'], 'findings': len(cp['research']['output']['bulgular']),
                   'draft_ready': not no_draft, 'delivered': False,
                   'elapsed_seconds': round(sum(s.get('elapsed_seconds', 0) for s in cp.values()), 2),
                   'cost': None})
    return 'Yeterli bulgu yok; taslak üretilmedi.' if no_draft else 'Kaynaklı inceleme ve taslak hazır; değerlendirmenizi bekliyor.'


def content_digest(lead):
    d = json.loads(lead.get('drafts') or '{}')
    return digest({'analysis': lead.get('analysis'), 'texts': {k: d.get(k) for k in
                   ('whatsapp', 'instagram', 'email_konu', 'email_govde')}, 'draft': lead.get('draft')})


def publish(store, jid):
    """Publish both outputs + one event + checkpoint in one transaction, or leave the lead alone."""
    with store.lock, store.db:
        row, data, cp = _run(store, jid)
        if row['published_at']:
            return
        lead = store.lead(row['lead_id'])
        _eligible(store, lead)
        if digest(snapshot(lead)) != row['input_digest']:
            raise Conflict('Firma veya taslak değişti; yeni sonuç mevcut kaydın üzerine yazılmadı.')
        result = cp['research']['output']
        drafts = cp.get('draft', {}).get('output')
        if result['karar'] == 'bulgu_var' and not drafts:
            raise Conflict('Taslak adımı tamamlanmadı; hazır olarak işaretlenmedi.')
        if drafts:
            for k in ('whatsapp', 'instagram', 'email_govde'):
                if not isinstance(drafts.get(k), str) or len(drafts[k].strip()) < 30:
                    raise Conflict('Eksik taslak kaydedilmedi.')
            drafts['marketing_job'] = jid
        stamp = now()
        store.db.execute('UPDATE leads SET analysis=?,analysis_at=?,drafts=?,draft=?,stage=?,updated_at=? WHERE id=?',
                         (_json(result), stamp, _json(drafts) if drafts else None, drafts['whatsapp'] if drafts else '',
                          'Taslak hazır' if drafts else 'İncelendi', stamp, lead['id']))
        store.db.execute("UPDATE approvals SET status='Reddedildi',decided_at=? WHERE lead_id=? AND status IN ('Bekliyor','Onaylandı')",
                         (stamp, lead['id']))
        store.db.execute('INSERT INTO events(lead_id,ts,title,detail) VALUES(?,?,?,?)',
                         (lead['id'], stamp, 'Jeff inceleme ve taslak işini tamamladı' if drafts else 'Jeff: yeterli bulgu yok',
                          'Kaynak alıntıları denetlendi; ihtiyaç varsayımdır. Gönderim yapılmadı. Görev: ' + jid))
        store.db.execute('UPDATE marketing_runs SET published_at=? WHERE job_id=?', (stamp, jid))


def review(store, lid, expected_digest, decision, text=None):
    if decision not in ('accepted', 'rejected', 'edited'):
        raise Conflict('Değerlendirme seçimi geçersiz.')
    with store.lock, store.db:
        lead = store.lead(lid)
        _eligible(store, lead)
        row = store.one('SELECT * FROM marketing_runs WHERE lead_id=? AND published_at IS NOT NULL ORDER BY rowid DESC LIMIT 1', (lid,))
        if not row or not lead.get('drafts') or content_digest(lead) != expected_digest:
            raise Conflict('Taslak değişti; güncel metni tekrar açıp değerlendirin.')
        # A subsequent independent rewrite is not this run's result.
        cp = json.loads(row['checkpoint'])
        if json.loads(lead['analysis']) != cp['research']['output'] or json.loads(lead['drafts']).get('marketing_job') != row['job_id']:
            raise Conflict('Araştırma değişti; yeni inceleme başlatın.')
        if decision == 'edited':
            if not isinstance(text, str) or not 30 <= len(text.strip()) <= 2000:
                raise Conflict('Düzenlenen taslak 30–2000 karakter olmalı.')
            d = json.loads(lead['drafts'])
            text, notes = contact.check_text(text, d.get('link'))
            d['whatsapp'], d['notes']['whatsapp'] = text, notes
            store.db.execute('UPDATE leads SET drafts=?,draft=?,updated_at=? WHERE id=?', (_json(d), text, now(), lid))
            store.db.execute("UPDATE approvals SET status='Reddedildi',decided_at=? WHERE lead_id=? AND status IN ('Bekliyor','Onaylandı')", (now(), lid))
            lead = store.lead(lid)
        new_digest = content_digest(lead)
        old = store.one('SELECT digest,decision FROM marketing_reviews WHERE job_id=? ORDER BY rowid DESC LIMIT 1', (row['job_id'],))
        if not old or old['digest'] != new_digest or old['decision'] != decision:
            store.db.execute('INSERT INTO marketing_reviews VALUES(?,?,?,?,?,?,?)',
                             ('mr' + uuid.uuid4().hex[:12], row['job_id'], new_digest, decision, 'panel_owner', lead['draft'], now()))
            label = {'accepted': 'Taslak uygun bulundu', 'rejected': 'Taslak uygun bulunmadı', 'edited': 'Taslak düzenlendi; yeniden değerlendirme gerekiyor'}[decision]
            store.db.execute('INSERT INTO events(lead_id,ts,title,detail) VALUES(?,?,?,?)', (lid, now(), label, 'Panel sahibi değerlendirmesi; gönderim yapılmadı.'))
        return {'digest': new_digest, 'decision': decision, 'delivered': False}


def views(store):
    out = {}
    for r in store.q('SELECT r.*,j.status,j.note FROM marketing_runs r JOIN jobs j ON j.id=r.job_id ORDER BY r.rowid'):
        cp = json.loads(r['checkpoint'])
        lead = store.lead(r['lead_id'])
        if not lead:
            continue
        current = content_digest(lead)
        matching = bool(r['published_at'] and json.loads(lead.get('drafts') or '{}').get('marketing_job') == r['job_id']
                        and json.loads(lead.get('analysis') or 'null') == cp.get('research', {}).get('output'))
        rev = store.one('SELECT digest,decision,created_at FROM marketing_reviews WHERE job_id=? ORDER BY rowid DESC LIMIT 1', (r['job_id'],))
        out[r['lead_id']] = {'job_id': r['job_id'], 'status': r['status'], 'note': r['note'],
                            'published_at': r['published_at'], 'current': matching, 'digest': current,
                            'review': rev if rev and rev['digest'] == current else None,
                            'steps': {k: {field: s.get(field) for field in ('state', 'elapsed_seconds', 'usage')} for k, s in cp.items()},
                            'delivered': False, 'cost': None}
    return out
