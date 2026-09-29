"""Does Jeff still have a working brain? Tries every model route with a one-word request.

Routes, in the order Jeff prefers them (see routes()):
  proxy       the Antigravity bridge on this machine (Jeff's main route today)
  opencode-go the OpenCode Go subscription (Jeff's configured spare tire)
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


def run(env, opener=urllib.request.urlopen, now=time.time, conflicts=()):
    results = []
    for name, url, key, model in routes(env):
        if name != 'proxy' and not key:
            results.append({'route': name, 'ok': False, 'ms': 0, 'detail': 'anahtar tanimli degil'})
            continue
        extra = {'x-opencode-session': str(uuid.uuid4())} if name == 'opencode-go' else None   # the relay rejects requests without it
        results.append(probe(name, url, key, model, opener=opener, extra_headers=extra))
    return {'checked_at': int(now()), 'routes': results, 'env_conflicts': list(conflicts)}


def summarize(report):
    """('all_ok' | 'spare_tire' | 'blind', plain-language sentence)"""
    by = {r['route']: r for r in report['routes']}
    working = [r['route'] for r in report['routes'] if r['ok']]
    if not working:
        return 'blind', 'Jeff hicbir yoldan dusunemiyor (ana kopru ve yedek yollar cevap vermiyor)'
    if by.get('proxy', {}).get('ok'):
        spare = [r for r in working if r != 'proxy']
        return 'all_ok', 'ana yol calisiyor' + (f', yedek: {", ".join(spare)}' if spare else ', YEDEK YOL YOK')
    return 'spare_tire', f'ana yol cevap vermiyor; Jeff yedek yolla ({", ".join(working)}) dusunuyor'


def write_report(report, path):
    tmp = f'{path}.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False)
    os.replace(tmp, path)


def watchdog_probe(path, max_age_seconds=45 * 60, now=time.time):
    """Adapter for system_watchdog: (ok, detail) from the last written report. A stale or unreadable
    report counts as a problem, so the checker itself cannot silently die."""
    def probe_fn():
        try:
            with open(path, encoding='utf-8') as f:
                report = json.load(f)
        except (OSError, ValueError):
            return False, 'model kontrol kaydi okunamadi'
        if now() - report.get('checked_at', 0) > max_age_seconds:
            return False, 'model kontrolu eskidi (calismiyor olabilir)'
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
    args = ap.parse_args(argv)
    files = [wd.load_env_file(f) for f in (args.env_file or ['/home/hermes/.hermes/gateway.env', '/home/hermes/.hermes/.env'])]
    env = {}
    for values in files:
        env.update(values)     # later file wins, exactly as Hermes loads .env over the service environment
    wanted = ['ANTIGRAVITY_API_KEY', 'OPENCODE_GO_API_KEY', 'GOOGLE_API_KEY', 'OPENROUTER_API_KEY']
    report = run(env, conflicts=env_conflicts(files, wanted))
    write_report(report, args.out)
    state, sentence = summarize(report)
    routes_txt = ', '.join(f"{r['route']}={'ok' if r['ok'] else r['detail']}({r['ms']}ms)" for r in report['routes'])
    extra = f" | UYARI iki dosyada farkli anahtar: {', '.join(report['env_conflicts'])}" if report.get('env_conflicts') else ''
    print(f'[model] {state}: {sentence} | {routes_txt}{extra}')
    return 0 if state != 'blind' else 1


if __name__ == '__main__':
    sys.exit(main())
