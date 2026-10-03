"""Official Instagram Business Discovery. Credentials never enter research data.

The credential can carry management permissions; this collector exercises GETs
only. Account management is a separate workflow, not a research side effect.
"""
import hashlib
import json
import os
import re
import stat
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ORIGIN = 'https://graph.facebook.com'
VERSION = 'v25.0'
MAX_BYTES = 1024 * 1024
MEDIA_LIMIT = 30
WINDOW_DAYS = 90
LIMITATION = 'Resmî Meta API: biyografi ve en son 30 medya öğesinin okunabilir yayıncı açıklamaları; 90 günlük kapsam ayrıca belirtilir. Görüntü, özel mesaj trafiği ve yanıt süresi incelenmedi.'


class Discovery(list):
    def __init__(self, pages, coverage):
        super().__init__(pages)
        self.coverage = coverage


class MetaError(Exception):
    """Only a fixed reason and numeric codes, never provider text or requests."""
    def __init__(self, reason, status=None, code=None):
        super().__init__(reason)
        self.reason, self.status, self.code = reason, status, code


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def credentials():
    default = Path(os.environ.get('CGOS_DATA', Path(__file__).resolve().parent.parent/'data'))/'meta-instagram.json'
    path = Path(os.environ.get('CGOS_META_INSTAGRAM_CREDENTIALS') or default)
    try:
        if os.name == 'posix' and stat.S_IMODE(path.stat().st_mode) & 0o077:
            raise MetaError('insecure_credentials')
        if path.stat().st_size > 8192:
            raise MetaError('invalid_credentials')
        raw = json.loads(path.read_text(encoding='utf-8-sig'))
        token, account = raw.get('access_token', ''), raw.get('business_account_id', '')
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{20,4096}', token) or not isinstance(account, str) or not re.fullmatch(r'\d{5,30}', account) or raw.get('version', VERSION) != VERSION:
            raise MetaError('invalid_credentials')
        return token, account
    except FileNotFoundError:
        raise MetaError('not_configured') from None
    except (OSError, ValueError, TypeError, AttributeError):
        raise MetaError('invalid_credentials') from None


def request(node, fields):
    token, _ = credentials()
    if not re.fullmatch(r'\d{5,30}', node):
        raise MetaError('invalid_account')
    url = ORIGIN+'/'+VERSION+'/'+node+'?'+urllib.parse.urlencode({'fields': fields})
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer '+token, 'Accept': 'application/json'}, method='GET')
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=20) as response:
            data = response.read(MAX_BYTES+1)
            if len(data) > MAX_BYTES:
                raise MetaError('response_too_large')
            raw = json.loads(data)
            if not isinstance(raw, dict) or 'error' in raw:
                raise MetaError('invalid_response')
            return raw
    except urllib.error.HTTPError as exc:
        code = None
        try:
            error = json.loads(exc.read(8192)).get('error', {})
            if type(error.get('code')) is int:
                code = error['code']
        except (ValueError, TypeError, AttributeError):
            pass
        # Token rejection is a connection problem, not missing business content.
        raise MetaError('credentials_rejected' if code == 190 else 'api_error', exc.code, code) from None
    except (urllib.error.URLError, OSError, TimeoutError):
        raise MetaError('transport_error') from None
    except (ValueError, TypeError):
        raise MetaError('invalid_response') from None


def permalink(url):
    """Generic /p or /reel links are accepted only with API publisher attestation."""
    try:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme == 'https' and parsed.hostname in ('instagram.com', 'www.instagram.com') and not (parsed.username or parsed.password or parsed.port) and re.fullmatch(r'/(?:p|reel)/[A-Za-z0-9_-]{5,80}/?', parsed.path):
            return 'https://www.instagram.com'+parsed.path.rstrip('/')+'/'
    except (ValueError, TypeError, AttributeError):
        pass
    return None


def published_at(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None or parsed.timestamp() > time.time()+300:
            return None
        return parsed.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError, AttributeError, OverflowError):
        return None


def discover(profile, identity_source):
    """Caller must first recheck the business's current official website link."""
    parsed = urllib.parse.urlsplit(profile)
    handle = parsed.path.strip('/')
    if profile != 'https://www.instagram.com/'+handle+'/' or not re.fullmatch(r'[a-z0-9_.]{1,30}', handle):
        raise MetaError('invalid_profile')
    _, account = credentials()
    fields = 'business_discovery.username('+handle+'){username,biography,website,media.limit('+str(MEDIA_LIMIT)+'){username,caption,permalink,timestamp}}'
    raw = request(account, fields).get('business_discovery')
    if not isinstance(raw, dict) or not isinstance(raw.get('username'), str) or raw['username'].lower() != handle:
        raise MetaError('publisher_mismatch')
    observed = int(time.time())
    common = {'observed_at': observed, 'identity_source': identity_source, 'identity_scope': 'official_website_link',
              'profile_url': profile, 'publisher_handle': handle, 'collection_method': 'meta_business_discovery'}
    pages = []
    def add(url, text, kind, timestamp=None):
        if not isinstance(text, str) or not 30 <= len(text) <= 12000:
            return
        pages.append({**common, 'url': url, 'text': text, 'links': [], 'source_kind': kind,
                      'text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'source_published_at': timestamp,
                      'content_scope': 'meta_business_discovery_publisher_caption' if kind == 'instagram_post' else 'meta_business_discovery_publisher_biography'})
    add(profile, raw.get('biography'), 'instagram_profile')
    media = raw.get('media', {}).get('data', []) if isinstance(raw.get('media'), dict) else []
    samples = media[:MEDIA_LIMIT] if isinstance(media, list) else []
    seen = set()
    duplicates = 0
    for post in samples:
        if not isinstance(post, dict) or not isinstance(post.get('username'), str) or post['username'].lower() != handle:
            continue
        url = permalink(post.get('permalink'))
        if url in seen:
            duplicates += 1
            continue
        if url:
            seen.add(url)
            add(url, post.get('caption'), 'instagram_post', published_at(post.get('timestamp')))
    posts = [page for page in pages if page['source_kind'] == 'instagram_post']
    recent = [page for page in posts if page['source_published_at'] and observed-datetime.fromisoformat(page['source_published_at']).timestamp() <= WINDOW_DAYS*86400]
    dates = sorted(page['source_published_at'] for page in posts if page['source_published_at'])
    # Reaching a cap or an older post does not prove that every post was returned.
    coverage = {'requested_media_limit': MEDIA_LIMIT, 'returned_media_items': len(samples), 'readable_captions': len(posts),
                'window_days': WINDOW_DAYS, 'captions_in_window': len(recent), 'undated_captions': sum(not page['source_published_at'] for page in posts),
                'oldest_publication': dates[0] if dates else None, 'newest_publication': dates[-1] if dates else None,
                'limit_reached': len(samples) == MEDIA_LIMIT, 'duplicate_permalinks': duplicates,
                'complete_window': 'unknown', 'pagination_followed': False}
    return Discovery(pages, coverage)


def attested_source(source, url):
    try:
        profile = source.get('profile_url', '')
        handle = urllib.parse.urlsplit(profile).path.strip('/')
        return bool(source.get('collection_method') == 'meta_business_discovery'
                and source.get('content_scope') == 'meta_business_discovery_publisher_caption'
                and profile == 'https://www.instagram.com/'+handle+'/' and re.fullmatch(r'[a-z0-9_.]{1,30}', handle)
                and source.get('publisher_handle') == handle and source.get('url') == url and permalink(url) == url
                    and 0 <= int(time.time())-int(source.get('observed_at', 0)) < 86400)
    except (ValueError, TypeError, AttributeError):
        return False
