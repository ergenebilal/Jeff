"""Source-backed clinic radar, canonical SQLite briefing and safe delivery."""
from dataclasses import dataclass
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import socket
import sqlite3
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen


class DuplicateReport(Exception):
    pass


@dataclass(frozen=True)
class Metric:
    value: int | str
    query: str
    snapshot_at: str


@dataclass(frozen=True)
class Briefing:
    report_id: str
    snapshot_at: str
    metrics: dict[str, Metric]
    priorities: list[str]
    text: str


def _domain(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username:
        raise ValueError('Valid source URL required')
    return parsed.hostname.lower().removeprefix('www.')


def _lead_key(candidate):
    domain = _domain(candidate['website'])
    company = ' '.join(candidate['company_name'].casefold().split())
    city = ' '.join(candidate['city'].casefold().split())
    return hashlib.sha256(f'{domain}|{company}|{city}'.encode()).hexdigest()


def _utc(now):
    if now.tzinfo is None:
        raise ValueError('Timezone-aware timestamp required')
    return now.astimezone(timezone.utc)


class BriefingStore:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS clinic_leads (
                    lead_id TEXT PRIMARY KEY, dedupe_key TEXT NOT NULL UNIQUE,
                    company_name TEXT NOT NULL, city TEXT NOT NULL, website TEXT NOT NULL,
                    source_url TEXT NOT NULL, observed_at TEXT NOT NULL,
                    contact_channel TEXT NOT NULL, contact_value TEXT NOT NULL,
                    verification_status TEXT NOT NULL, fit_score INTEGER NOT NULL,
                    evidence TEXT NOT NULL, problem_hypothesis TEXT NOT NULL,
                    draft_status TEXT NOT NULL, outreach_status TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS report_deliveries (
                    report_id TEXT PRIMARY KEY, content_digest TEXT NOT NULL,
                    status TEXT NOT NULL, chunk_count INTEGER NOT NULL,
                    sent_chunks INTEGER NOT NULL, claimed_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL, failure_reason TEXT
                );
            ''')

    def ingest(self, candidates, now):
        now_iso = _utc(now).isoformat()
        created = updated = 0
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for candidate in candidates:
                if created >= 10:
                    break
                if _domain(candidate['website']) != _domain(candidate['source_url']):
                    raise ValueError('Source must belong to the official website domain')
                if not candidate['company_name'].strip() or not candidate['city'].strip():
                    raise ValueError('Company and city are required')
                channel = candidate.get('contact_channel', 'none')
                if channel not in ('email', 'phone', 'website', 'none'):
                    raise ValueError('Unsupported contact channel')
                contact = candidate.get('contact_value', '')
                if channel == 'email' and contact and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', contact):
                    raise ValueError('Invalid email contact')
                score = candidate.get('fit_score', 0)
                if not isinstance(score, int) or not 0 <= score <= 100:
                    raise ValueError('Fit score must be 0..100')
                key = _lead_key(candidate)
                existing = db.execute('SELECT lead_id,observed_at,draft_status,outreach_status '
                                      'FROM clinic_leads WHERE dedupe_key=?', (key,)).fetchone()
                status = candidate.get('verification_status', 'UNVERIFIED')
                if status not in ('VERIFIED', 'UNVERIFIED'):
                    raise ValueError('Invalid contact verification status')
                if not contact:
                    status = 'UNVERIFIED'
                lead_id = existing['lead_id'] if existing else key[:24]
                observed_at = existing['observed_at'] if existing else now_iso
                draft_status = existing['draft_status'] if existing else 'NOT_READY'
                outreach_status = existing['outreach_status'] if existing else 'NOT_SENT'
                db.execute('''INSERT INTO clinic_leads VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(dedupe_key) DO UPDATE SET
                    source_url=excluded.source_url,contact_channel=excluded.contact_channel,
                    contact_value=excluded.contact_value,
                    verification_status=excluded.verification_status,
                    fit_score=excluded.fit_score,evidence=excluded.evidence,
                    problem_hypothesis=excluded.problem_hypothesis,updated_at=excluded.updated_at''',
                    (lead_id, key, candidate['company_name'].strip(), candidate['city'].strip(),
                     candidate['website'], candidate['source_url'], observed_at, channel, contact,
                     status, score, candidate.get('evidence', ''),
                     candidate.get('problem_hypothesis', ''), draft_status, outreach_status,
                     now_iso))
                if existing:
                    updated += 1
                else:
                    created += 1
        return {'created': created, 'updated': updated}

    def leads(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM clinic_leads ORDER BY observed_at,lead_id')]

    def snapshot(self, now):
        now = _utc(now)
        stamp = now.isoformat()
        yesterday = (now.date() - timedelta(days=1)).isoformat()
        today = now.date().isoformat()
        past_day = (now - timedelta(hours=24)).isoformat()
        specs = {
            'verified_yesterday': (
                "SELECT COUNT(*) FROM task_records WHERE status='verified' AND updated_at>=? AND updated_at<?",
                (yesterday, today)),
            'failed_stuck': (
                "SELECT COUNT(*) FROM task_records WHERE status IN ('failed','escalated','reconciling')",
                ()),
            'new_leads': (
                'SELECT COUNT(*) FROM clinic_leads WHERE observed_at>=? AND observed_at<=?',
                (past_day, stamp)),
            'ready_drafts': (
                "SELECT COUNT(*) FROM clinic_leads WHERE draft_status='READY'", ()),
            'pending_approvals': (
                "SELECT COUNT(*) FROM task_records WHERE status='waiting_approval'", ()),
            'pablo_health': ('SELECT agent,status,last_seen FROM alfred_heartbeat WHERE id=1', ()),
        }
        metrics = {}
        if self.path.exists():
            try:
                with self.connect() as db:
                    db.execute('BEGIN')  # One consistent SQLite read snapshot.
                    for name, (query, params) in specs.items():
                        try:
                            row = db.execute(query, params).fetchone()
                            if name == 'pablo_health':
                                value = ('UNKNOWN' if row is None else
                                         'online' if row['agent'] == 'pablo' and row['status'] == 'ok'
                                         and now.timestamp() - row['last_seen'] < 60 else 'offline')
                            else:
                                value = row[0]
                        except (sqlite3.DatabaseError, TypeError, KeyError):
                            value = 'UNKNOWN'
                        metrics[name] = Metric(value, query, stamp)
                    priorities = self._priorities(db)
            except sqlite3.DatabaseError:
                metrics = {name: Metric('UNKNOWN', query, stamp)
                           for name, (query, _) in specs.items()}
                priorities = []
        else:
            metrics = {name: Metric('UNKNOWN', query, stamp)
                       for name, (query, _) in specs.items()}
            priorities = []
        labels = [('pablo_health', 'Sistem sağlığı'),
                  ('verified_yesterday', 'Dün doğrulanan işler'),
                  ('failed_stuck', 'Başarısız veya takılmış işler'),
                  ('new_leads', 'Yeni leadler'), ('ready_drafts', 'Hazır taslaklar'),
                  ('pending_approvals', 'Onay bekleyenler')]
        lines = [f'Yönetici brifingi — {stamp}', f'Rapor ID: briefing-{now.date().isoformat()}']
        for name, label in labels:
            metric = metrics[name]
            value = 'UNKNOWN (data unavailable)' if metric.value == 'UNKNOWN' else metric.value
            lines.append(f'{label}: {value} [snapshot: {metric.snapshot_at}; query: {name}]')
        lines.append('Bugünün üç önceliği:')
        lines.extend(f'{index}. {item}' for index, item in enumerate(priorities[:3], 1))
        if not priorities:
            available = (metrics['failed_stuck'].value != 'UNKNOWN'
                         and metrics['new_leads'].value != 'UNKNOWN')
            lines.append('Kayıtlı öncelik yok' if available else 'UNKNOWN (data unavailable)')
        return Briefing(f'briefing-{now.date().isoformat()}', stamp, metrics,
                        priorities[:3], '\n'.join(lines))

    @staticmethod
    def _priorities(db):
        items = []
        try:
            task_rows = db.execute('''SELECT goal,status FROM task_records
                WHERE status IN ('escalated','reconciling','waiting_approval','failed')
                ORDER BY CASE status WHEN 'escalated' THEN 0 WHEN 'reconciling' THEN 1
                    WHEN 'waiting_approval' THEN 2 ELSE 3 END,updated_at DESC LIMIT 3''').fetchall()
            items = [f"{row['status']}: {row['goal']}" for row in task_rows]
        except sqlite3.DatabaseError:
            pass
        if len(items) < 3:
            try:
                lead_rows = db.execute('''SELECT company_name,city FROM clinic_leads
                    WHERE draft_status='NOT_READY' ORDER BY fit_score DESC,observed_at DESC LIMIT ?''',
                    (3 - len(items),)).fetchall()
                items.extend(f"Taslak incele: {row['company_name']} ({row['city']})"
                             for row in lead_rows)
            except sqlite3.DatabaseError:
                pass
        return items

    def claim_report(self, report_id, text, count):
        stamp = datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                db.execute('INSERT INTO report_deliveries VALUES(?,?,?,?,?,?,?,?)',
                           (report_id, hashlib.sha256(text.encode()).hexdigest(), 'SENDING',
                            count, 0, stamp, stamp, None))
            except sqlite3.IntegrityError as exc:
                raise DuplicateReport(report_id) from exc

    def delivery_progress(self, report_id, status, sent_chunks, reason=None):
        with self.connect() as db:
            db.execute('''UPDATE report_deliveries SET status=?,sent_chunks=?,updated_at=?,
                          failure_reason=? WHERE report_id=?''',
                       (status, sent_chunks, datetime.now(timezone.utc).isoformat(),
                        reason, report_id))


def _public_source_url(url, allow_loopback=False):
    parsed = urlsplit(url)
    if parsed.scheme not in (('http', 'https') if allow_loopback else ('https',)):
        raise ValueError('Public sources require HTTPS')
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Invalid source URL')
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global and not (allow_loopback and ip.is_loopback):
            raise ValueError('Source URL resolves to a non-public address')


class _SafeRedirect(HTTPRedirectHandler):
    def __init__(self, allow_loopback):
        self.allow_loopback = allow_loopback

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _public_source_url(newurl, self.allow_loopback)
        if _domain(newurl) != _domain(req.full_url):
            raise ValueError('Cross-domain redirect rejected')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def scan_sources(sources, now, allow_loopback=False):
    """Read official clinic pages; no forms, contact attempts or inferred emails."""
    candidates = []
    opener = build_opener(_SafeRedirect(allow_loopback))
    for source in sources[:10]:
        url = source['source_url']
        if _domain(url) != _domain(source['website']):
            raise ValueError('Source domain must match website')
        _public_source_url(url, allow_loopback)
        request = Request(url, headers={'User-Agent': 'JeffClinicRadar/1.0 (read-only)'})
        try:
            with opener.open(request, timeout=5) as response:
                if response.status != 200:
                    continue
                page = response.read(200_000).decode('utf-8', errors='replace')
        except (HTTPError, OSError):
            continue
        company_present = source['company_name'].casefold() in page.casefold()
        contact = source.get('contact_value', '')
        contact_present = bool(contact and contact.casefold() in page.casefold())
        candidate = dict(source)
        candidate['verification_status'] = ('VERIFIED' if company_present and contact_present
                                            else 'UNVERIFIED')
        candidate['evidence'] = ('Official page HTTP 200; company name '
                                 + ('present' if company_present else 'not located')
                                 + '; contact ' + ('present' if contact_present else 'not located'))
        candidate['observed_at'] = _utc(now).isoformat()
        candidates.append(candidate)
    return candidates


def split_message(message, max_chars=4096):
    if max_chars < 1:
        raise ValueError('Character limit must be positive')
    parts = []
    current = ''
    for line in message.split('\n'):
        if len(line) > max_chars:
            if current:
                parts.append(current)
                current = ''
            parts.extend(line[i:i + max_chars] for i in range(0, len(line), max_chars))
            continue
        proposed = current + ('\n' if current else '') + line
        if len(proposed) > max_chars:
            parts.append(current)
            current = line
        else:
            current = proposed
    if current or not parts:
        parts.append(current)
    return parts


class TelegramDelivery:
    def __init__(self, store, token, chat_id, endpoint=None, sleep=time.sleep):
        if not token or not chat_id:
            raise ValueError('Telegram token and admin chat ID required')
        self.store = store
        self.chat_id = str(chat_id)
        self.endpoint = endpoint or f'https://api.telegram.org/bot{token}/sendMessage'
        host = urlsplit(self.endpoint).hostname
        if host not in ('api.telegram.org', '127.0.0.1', 'localhost', '::1'):
            raise ValueError('Telegram endpoint must be official or loopback')
        if host == 'api.telegram.org' and urlsplit(self.endpoint).scheme != 'https':
            raise ValueError('Official Telegram endpoint requires HTTPS')
        self.sleep = sleep

    def send(self, report_id, message):
        chunks = split_message(message)
        self.store.claim_report(report_id, message, len(chunks))
        sent = 0
        try:
            for chunk in chunks:
                payload = json.dumps({'chat_id': self.chat_id, 'text': chunk}).encode()
                for attempt in range(3):
                    request = Request(self.endpoint, data=payload,
                                      headers={'Content-Type': 'application/json'}, method='POST')
                    try:
                        with urlopen(request, timeout=10) as response:
                            result = json.load(response)
                            if not result.get('ok'):
                                raise RuntimeError('Telegram did not confirm delivery')
                        sent += 1
                        self.store.delivery_progress(report_id, 'SENDING', sent)
                        break
                    except HTTPError as exc:
                        if exc.code == 429 and attempt < 2:
                            self.sleep(2 ** attempt)
                            continue
                        raise
            self.store.delivery_progress(report_id, 'SENT', sent)
            return {'status': 'SENT', 'chunks': sent}
        except Exception as exc:
            # A timeout can mean accepted-but-unacknowledged. Never blindly resend.
            self.store.delivery_progress(report_id, 'UNKNOWN', sent, type(exc).__name__)
            raise
