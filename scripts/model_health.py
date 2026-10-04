"""Does Jeff still have a working brain? Tries every model route with a one-word request.

Routes are probes; the preferred route is read from the active configuration:
  proxy       the Antigravity bridge on this machine
  opencode-go the OpenCode Go subscription
  gemini      Google's official Gemini API, directly
  openrouter  OpenRouter

Each probe is a real (tiny) completion, because a bridge that answers /v1/models can still have no
working Google account behind it. API keys come from an env file and are never printed or logged.

    python scripts/model_health.py --env-file /home/hermes/.hermes/gateway.env --out /home/hermes/logs/model_health.json

The JSON file is read by the watchdog: it alerts when the main route is down (Jeff is on his spare
tire) and much louder when every route is down (Jeff cannot think at all).
"""
import argparse
import json
import math
import os
import sys
import time
import uuid
import urllib.error
import urllib.request

try:  # imported as a package (tests) or run from the scripts folder (server)
    from scripts import system_watchdog as wd
except ImportError:  # pragma: no cover
    import system_watchdog as wd

PROMPT = 'Reply with the single word: ok'
# Thinking models spend tokens on reasoning before the visible answer; 8 tokens would look like an empty reply.
MAX_TOKENS = 400
USER_AGENT = 'CyberGene-model-health/1.0'


def _post(url, headers, body, timeout, opener):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method='POST',
                                 headers={'Content-Type': 'application/json', **headers})
    with opener(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8', 'replace') or '{}')


def _answered(payload):
    try:
        return bool(payload['choices'][0]['message']['content'].strip())
    except (KeyError, IndexError, TypeError, AttributeError):
        return False


def probe(name, url, key, model, timeout=25, opener=urllib.request.urlopen, extra_headers=None):
    """One tiny chat completion. Returns {'route','ok','ms','detail'}; never includes the key."""
    started = time.time()
    headers = {'Authorization': f'Bearer {key}'} if key else {}
    headers['User-Agent'] = USER_AGENT
    headers.update(extra_headers or {})
    try:
        status, payload = _post(url, headers, {'model': model, 'max_tokens': MAX_TOKENS, 'temperature': 0,
                                               'messages': [{'role': 'user', 'content': PROMPT}]}, timeout, opener)
        ok, detail = _answered(payload), f'HTTP {status}'
        if not ok:
            detail += ', bos cevap'
    except urllib.error.HTTPError as err:
        ok, detail = False, f'HTTP {err.code}'
    except Exception as exc:
        ok, detail = False, type(exc).__name__
    return {'route': name, 'ok': ok, 'ms': int((time.time() - started) * 1000), 'detail': detail}


def routes(env):
    """The routes to test, built from the environment (a route without its key is reported as not configured)."""
    return [
        ('proxy', 'http://127.0.0.1:8999/v1/chat/completions', env.get('ANTIGRAVITY_API_KEY', ''),
         env.get('MODEL_PROXY', 'gemini-3.8-flash-high')),
        ('opencode-go', 'https://opencode.ai/zen/go/v1/chat/completions', env.get('OPENCODE_GO_API_KEY', ''),
         env.get('MODEL_OPENCODE', 'deepseek-v4-flash')),
        ('gemini', 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
         env.get('GOOGLE_API_KEY', ''), env.get('MODEL_GEMINI', 'gemini-2.5-flash')),
        ('openrouter', 'https://openrouter.ai/api/v1/chat/completions', env.get('OPENROUTER_API_KEY', ''),
         env.get('MODEL_OPENROUTER', 'google/gemini-2.5-flash')),
    ]


PROVIDER_TO_ROUTE = {'antigravity': 'proxy', 'opencode-go': 'opencode-go', 'gemini': 'gemini', 'openrouter': 'openrouter'}


def main_route_from_config(path):
    """Which route Jeff prefers, read from his own config (model.provider), so the alerts follow a change of main route."""
    try:
        import yaml
        provider = (yaml.safe_load(open(path, encoding='utf-8')) or {}).get('model', {}).get('provider', '')
    except Exception:
        return 'unknown'
    return PROVIDER_TO_ROUTE.get(str(provider).strip().lower(), 'unknown')


def env_conflicts(files, wanted):
    """Names in `wanted` that two env files define with DIFFERENT values. Hermes reads ~/.hermes/.env on top of the
    service's gateway.env (override), so a stale key in one of them silently beats the good key in the other."""
    seen, conflicts = {}, []
    for values in files:
        for name in wanted:
            if values.get(name):
                if name in seen and seen[name] != values[name] and name not in conflicts:
                    conflicts.append(name)
                seen.setdefault(name, values[name])
    return conflicts


def run(env, opener=urllib.request.urlopen, now=time.time, conflicts=(), main='proxy'):
    results = []
    for name, url, key, model in routes(env):
        if name != 'proxy' and not key:
            results.append({'route': name, 'ok': False, 'ms': 0, 'detail': 'anahtar tanimli degil'})
            continue
        extra = {'x-opencode-session': str(uuid.uuid4())} if name == 'opencode-go' else None   # the relay rejects requests without it
        results.append(probe(name, url, key, model, opener=opener, extra_headers=extra))
    report = {'checked_at': int(now()), 'routes': results, 'env_conflicts': list(conflicts), 'main': main}
    report.update(health_snapshot(report, now=now))
    return report


def _valid_probe_time(value):
    return type(value) in (int,float) and math.isfinite(value) and value >= 0


def _probe_inventory(report):
    """Accept only explicit boolean results for distinct configured routes."""
    known=set(PROVIDER_TO_ROUTE.values())
    if not isinstance(report,dict) or not isinstance(report.get('main'),str) or report['main'] not in known:
        return None
    rows=report.get('routes')
    if not isinstance(rows,list) or any(not isinstance(r,dict) or
            not isinstance(r.get('route'),str) or r['route'] not in known or
            type(r.get('ok')) is not bool for r in rows):
        return None
    names=[r['route'] for r in rows]
    if len(set(names))!=len(names) or report['main'] not in names:
        return None
    conflicts=report.get('env_conflicts',[])
    if not isinstance(conflicts,list) or any(name not in
            ('ANTIGRAVITY_API_KEY','OPENCODE_GO_API_KEY','GOOGLE_API_KEY','OPENROUTER_API_KEY') for name in conflicts):
        return None
    return rows


def health_snapshot(report, max_age_seconds=30 * 60, now=time.time):
    """Probe availability is distinct from the route used by a real session."""
    report=report if isinstance(report,dict) else {}
    preferred = report.get('main', 'unknown')
    observed = report.get('checked_at')
    rows = _probe_inventory(report)
    available = [r['route'] for r in rows or [] if r['ok'] is True]
    fresh = _valid_probe_time(observed) and 0 <= now() - observed <= max_age_seconds
    primary = next((r for r in rows or [] if r['route']==preferred),None)
    reliable = fresh and primary is not None and not report.get('env_conflicts')
    if not reliable:
        status = 'unknown'
    elif primary.get('ok') is True:
        status = 'healthy'
    elif available:
        status = 'degraded'
    else:
        status = 'unavailable'
    return {'preferred_route': preferred, 'preferred_status': 'unknown' if not reliable else
            'healthy' if primary['ok'] is True else 'unavailable', 'available_routes': available if reliable else [],
            'observed_at': observed, 'health_status': status, 'actual_session_route': 'unknown',
            'last_success_at': report.get('last_success_at', {})}


def summarize(report):
    """('all_ok' | 'spare_tire' | 'blind' | 'unknown', plain-language sentence)"""
    rows=_probe_inventory(report)
    if rows is None or report.get('env_conflicts'):
        return 'unknown','model kontrol sonucu bilinmiyor'
    by = {r['route']: r for r in rows}
    main = report['main']
    working = [r['route'] for r in rows if r['ok'] is True]
    if not working:
        return 'blind', 'Jeff hicbir yoldan dusunemiyor (ana kopru ve yedek yollar cevap vermiyor)'
    if by.get(main, {}).get('ok'):
        spare = [r for r in working if r != main]
        return 'all_ok', f'ana yol ({main}) calisiyor' + (f', yedek: {", ".join(spare)}' if spare else ', YEDEK YOL YOK')
    return 'spare_tire', f'ana yol ({main}) cevap vermiyor; probe testinde yedek yolla ({", ".join(working)}) cevap alinabildi; gercek oturum rotasi ayri makbuz gerektirir'


def write_report(report, path):
    try:
        with open(path, encoding='utf-8') as previous:
            successes = json.load(previous).get('last_success_at', {})
        if not isinstance(successes, dict):
            successes = {}
    except (OSError, ValueError, AttributeError):
        successes = {}
    for route in report.get('routes', []):
        if route.get('ok') is True:
            successes[route['route']] = report['checked_at']
    report['last_success_at'] = successes
    tmp = f'{path}.{uuid.uuid4().hex}.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False)
    os.replace(tmp, path)


def watchdog_probe(path, max_age_seconds=30 * 60, now=time.time):
    """Adapter for system_watchdog: (ok, detail) from the last written report. A stale or unreadable
    report counts as a problem, so the checker itself cannot silently die."""
    def probe_fn():
        try:
            with open(path, encoding='utf-8') as f:
                report = json.load(f)
        except (OSError, ValueError):
            return False, 'model kontrol kaydi okunamadi'
        if not isinstance(report,dict) or not _valid_probe_time(report.get('checked_at')):
            return False, 'model kontrol zamani bilinmiyor'
        age=now()-report['checked_at']
        if age < 0:
            return False, 'model kontrol zamani gelecekte; sonuc bilinmiyor'
        if age > max_age_seconds:
            return False, 'model kontrolu eskidi (calismiyor olabilir)'
        if _probe_inventory(report) is None:
            return False, 'model kontrol sonucu bilinmiyor'
        if report.get('env_conflicts'):
            return False, 'iki ayar dosyasinda FARKLI anahtar: ' + ', '.join(report['env_conflicts']) + ' (Jeff .env dosyasindakini kullanir)'
        state, sentence = summarize(report)
        # Anything but 'main route works' deserves a message: on the spare tire Jeff still answers, but a second
        # failure would leave him blind, and that is worth knowing before it happens.
        return state == 'all_ok', sentence
    return probe_fn


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--env-file', action='append',
                    help='env file(s); later ones override earlier ones, like Hermes does (default: gateway.env then .env)')
    ap.add_argument('--out', default='/home/hermes/logs/model_health.json')
    ap.add_argument('--config', default='/home/hermes/.hermes/config.yaml', help="Jeff's config; model.provider decides the main route")
    args = ap.parse_args(argv)
    files = [wd.load_env_file(f) for f in (args.env_file or ['/home/hermes/.hermes/gateway.env', '/home/hermes/.hermes/.env'])]
    env = {}
    for values in files:
        env.update(values)     # later file wins, exactly as Hermes loads .env over the service environment
    wanted = ['ANTIGRAVITY_API_KEY', 'OPENCODE_GO_API_KEY', 'GOOGLE_API_KEY', 'OPENROUTER_API_KEY']
    report = run(env, conflicts=env_conflicts(files, wanted), main=main_route_from_config(args.config))
    write_report(report, args.out)
    state, sentence = summarize(report)
    routes_txt = ', '.join(f"{r['route']}={'ok' if r['ok'] else r['detail']}({r['ms']}ms)" for r in report['routes'])
    extra = f" | UYARI iki dosyada farkli anahtar: {', '.join(report['env_conflicts'])}" if report.get('env_conflicts') else ''
    print(f'[model] {state}: {sentence} | {routes_txt}{extra}')
    return 0 if state != 'blind' else 1


if __name__ == '__main__':
    sys.exit(main())
