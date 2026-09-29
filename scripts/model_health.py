"""Does Jeff still have a working brain? Tries every model route with a one-word request.

Routes, in the order Jeff prefers them (see ROUTES):
  proxy       the Antigravity bridge on this machine (Jeff's main route today)
  gemini      Google's official Gemini API, directly
  openrouter  OpenRouter, the configured fallback

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
import urllib.error
import urllib.request

try:  # imported as a package (tests) or run from the scripts folder (server)
    from scripts import system_watchdog as wd
except ImportError:  # pragma: no cover
    import system_watchdog as wd

PROMPT = 'Reply with the single word: ok'


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
    headers.update(extra_headers or {})
    try:
        status, payload = _post(url, headers, {'model': model, 'max_tokens': 8, 'temperature': 0,
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
        ('gemini', 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
         env.get('GOOGLE_API_KEY', ''), env.get('MODEL_GEMINI', 'gemini-2.5-flash')),
        ('openrouter', 'https://openrouter.ai/api/v1/chat/completions', env.get('OPENROUTER_API_KEY', ''),
         env.get('MODEL_OPENROUTER', 'google/gemini-2.5-flash')),
    ]


def run(env, opener=urllib.request.urlopen, now=time.time):
    results = []
    for name, url, key, model in routes(env):
        if name != 'proxy' and not key:
            results.append({'route': name, 'ok': False, 'ms': 0, 'detail': 'anahtar tanimli degil'})
            continue
        results.append(probe(name, url, key, model, opener=opener))
    return {'checked_at': int(now()), 'routes': results}


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
        state, sentence = summarize(report)
        return state != 'blind', sentence
    return probe_fn


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--env-file', default='/home/hermes/.hermes/gateway.env')
    ap.add_argument('--out', default='/home/hermes/logs/model_health.json')
    args = ap.parse_args(argv)
    env = {**wd.load_env_file(args.env_file)}
    report = run(env)
    write_report(report, args.out)
    state, sentence = summarize(report)
    routes_txt = ', '.join(f"{r['route']}={'ok' if r['ok'] else r['detail']}({r['ms']}ms)" for r in report['routes'])
    print(f'[model] {state}: {sentence} | {routes_txt}')
    return 0 if state != 'blind' else 1


if __name__ == '__main__':
    sys.exit(main())
