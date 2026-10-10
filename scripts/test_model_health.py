import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path

from scripts import model_health as mh

KEY = 'fixture-model-key-1234'


class FakeResponse(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def ok_opener(req, timeout):
    return FakeResponse(json.dumps({'choices': [{'message': {'content': 'ok'}}]}).encode())


def status_opener(code):
    def opener(req, timeout):
        raise urllib.error.HTTPError(req.full_url, code, 'x', {}, None)
    return opener


def by_url(mapping):
    def opener(req, timeout):
        for needle, fn in mapping.items():
            if needle in req.full_url:
                return fn(req, timeout)
        raise OSError('no route')
    return opener


class ProbeTests(unittest.TestCase):
    def test_success_needs_a_real_answer(self):
        r = mh.probe('p', 'http://x/v1/chat/completions', KEY, 'm', opener=ok_opener)
        self.assertTrue(r['ok'])

    def test_empty_answer_is_a_failure_even_with_http_200(self):
        empty = lambda req, timeout: FakeResponse(json.dumps({'choices': [{'message': {'content': ''}}]}).encode())  # noqa: E731
        r = mh.probe('p', 'http://x', KEY, 'm', opener=empty)
        self.assertFalse(r['ok'])
        self.assertIn('bos cevap', r['detail'])

    def test_http_errors_and_network_errors_are_reported_without_the_key(self):
        for opener, expect in ((status_opener(401), 'HTTP 401'), (status_opener(429), 'HTTP 429'),
                               (lambda req, timeout: (_ for _ in ()).throw(OSError('boom')), 'OSError')):
            r = mh.probe('p', 'http://x', KEY, 'm', opener=opener)
            self.assertFalse(r['ok'])
            self.assertEqual(r['detail'], expect)
            self.assertNotIn(KEY, json.dumps(r))

    def test_garbage_json_is_a_failure(self):
        junk = lambda req, timeout: FakeResponse(b'not json')  # noqa: E731
        self.assertFalse(mh.probe('p', 'http://x', KEY, 'm', opener=junk)['ok'])


class RunAndSummaryTests(unittest.TestCase):
    ENV = {'GOOGLE_API_KEY': KEY, 'OPENROUTER_API_KEY': KEY, 'OPENCODE_GO_API_KEY': KEY}

    def test_missing_key_means_route_not_configured_not_crash(self):
        report = mh.run({}, opener=by_url({'127.0.0.1': ok_opener}))
        detail = {r['route']: r['detail'] for r in report['routes']}
        self.assertEqual(detail['opencode-go'], 'anahtar tanimli degil')

    def test_unselected_provider_keys_never_trigger_extra_probes(self):
        sent=[]
        def opener(req,timeout):
            sent.append((req.full_url,json.loads(req.data),req.headers))
            return ok_opener(req,timeout)
        report=mh.run(self.ENV,opener=opener,main='opencode-go')
        self.assertEqual({row['route'] for row in report['routes']},{'proxy','opencode-go'})
        self.assertEqual(len(sent),2)
        go=next(item for item in sent if 'opencode.ai' in item[0])
        self.assertEqual(go[1]['model'],'deepseek-v4.1-flash')
        self.assertIn('hermes-agent',go[2]['User-agent'])
        self.assertTrue(go[2]['X-opencode-session'])
        self.assertFalse(any('googleapis' in url or 'openrouter' in url for url,_,_ in sent))

    def test_all_ok_with_spares(self):
        report = mh.run(self.ENV, opener=ok_opener)
        state, sentence = mh.summarize(report)
        self.assertEqual(state, 'all_ok')
        self.assertIn('opencode-go', sentence)

    def test_main_route_up_but_no_spare_is_called_out(self):
        report = mh.run({}, opener=by_url({'127.0.0.1': ok_opener}))
        state, sentence = mh.summarize(report)
        self.assertEqual(state, 'all_ok')
        self.assertIn('YEDEK YOL YOK', sentence)

    def test_main_route_down_means_spare_tire(self):
        opener = by_url({'127.0.0.1': status_opener(503), 'opencode.ai': ok_opener, 'googleapis': status_opener(403),
                         'openrouter': status_opener(402)})
        state, sentence = mh.summarize(mh.run(self.ENV, opener=opener))
        self.assertEqual(state, 'spare_tire')
        self.assertIn('opencode-go', sentence)

    def test_opencode_route_sends_the_session_header_the_relay_requires(self):
        seen = {}

        def opener(req, timeout):
            seen[req.full_url] = {k.lower(): v for k, v in req.header_items()}
            return ok_opener(req, timeout)
        mh.run(self.ENV, opener=opener)
        headers = seen['https://opencode.ai/zen/go/v1/chat/completions']
        self.assertTrue(headers.get('x-opencode-session'))
        self.assertNotIn('x-opencode-session', seen['http://127.0.0.1:8999/v1/chat/completions'])
        self.assertEqual(headers['user-agent'], mh.USER_AGENT)

    def test_requests_leave_room_for_thinking_models(self):
        bodies = []

        def opener(req, timeout):
            bodies.append(json.loads(req.data))
            return ok_opener(req, timeout)
        mh.run(self.ENV, opener=opener)
        self.assertTrue(all(b['max_tokens'] >= 200 for b in bodies))

    def test_everything_down_is_blind(self):
        state, sentence = mh.summarize(mh.run(self.ENV, opener=status_opener(500)))
        self.assertEqual(state, 'blind')
        self.assertIn('hicbir yoldan dusunemiyor', sentence)


class WatchdogAdapterTests(unittest.TestCase):
    def report_file(self, d, routes, checked_at):
        p = Path(d) / 'model_health.json'
        p.write_text(json.dumps({'checked_at': checked_at, 'main':'proxy', 'routes': routes}))
        return p

    def test_ok_spare_tire_blind_stale_and_missing(self):
        good = {'route': 'proxy', 'ok': True, 'ms': 1, 'detail': ''}
        bad_proxy = {'route': 'proxy', 'ok': False, 'ms': 1, 'detail': 'HTTP 503'}
        gem = {'route': 'gemini', 'ok': True, 'ms': 1, 'detail': ''}
        gem_bad = {'route': 'gemini', 'ok': False, 'ms': 1, 'detail': 'HTTP 401'}
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(mh.watchdog_probe(self.report_file(d, [good, gem], 1000), now=lambda: 1100)()[0])
            ok, text = mh.watchdog_probe(self.report_file(d, [bad_proxy, gem], 1000), now=lambda: 1100)()
            self.assertFalse(ok)                     # still thinking on the spare, but worth a message
            self.assertIn('yedek yolla', text)
            self.assertFalse(mh.watchdog_probe(self.report_file(d, [bad_proxy, gem_bad], 1000), now=lambda: 1100)()[0])
            ok, text = mh.watchdog_probe(self.report_file(d, [good], 1000), now=lambda: 1000 + 3 * 3600)()
            self.assertFalse(ok)
            self.assertIn('eskidi', text)
        self.assertFalse(mh.watchdog_probe('/nonexistent/x.json')()[0])

    def test_env_files_that_disagree_are_reported_and_alert(self):
        good, stale = {'OPENCODE_GO_API_KEY': 'new'}, {'OPENCODE_GO_API_KEY': 'old', 'OTHER': 'x'}
        self.assertEqual(mh.env_conflicts([good, stale], ['OPENCODE_GO_API_KEY']), ['OPENCODE_GO_API_KEY'])
        self.assertEqual(mh.env_conflicts([good, {'OPENCODE_GO_API_KEY': 'new'}], ['OPENCODE_GO_API_KEY']), [])
        self.assertEqual(mh.env_conflicts([good, {}], ['OPENCODE_GO_API_KEY']), [])         # only one file defines it: fine
        with tempfile.TemporaryDirectory() as d:
            report = mh.run({}, opener=by_url({'127.0.0.1': ok_opener}), conflicts=['OPENCODE_GO_API_KEY'])
            report['checked_at'] = 1000
            path = Path(d) / 'r.json'
            path.write_text(json.dumps(report))
            ok, text = mh.watchdog_probe(path, now=lambda: 1100)()
        self.assertFalse(ok)           # main route fine, but the files disagree: still worth a message
        self.assertIn('FARKLI anahtar', text)

    def test_main_route_follows_jeffs_config_and_alerts_follow_it(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / 'config.yaml'
            cfg.write_text('model:' + chr(10) + '  provider: opencode-go' + chr(10))
            self.assertEqual(mh.main_route_from_config(cfg), 'opencode-go')
            cfg.write_text('model:' + chr(10) + '  provider: antigravity' + chr(10))
            self.assertEqual(mh.main_route_from_config(cfg), 'proxy')
            self.assertEqual(mh.main_route_from_config(Path(d) / 'missing.yaml'), 'unknown')
        env = {'GOOGLE_API_KEY': KEY, 'OPENROUTER_API_KEY': KEY, 'OPENCODE_GO_API_KEY': KEY}
        # main = opencode-go: the bridge being down is only a bad SPARE, not an emergency
        opener = by_url({'127.0.0.1': status_opener(500), 'opencode.ai': ok_opener})
        state, sentence = mh.summarize(mh.run(env, opener=opener, main='opencode-go'))
        self.assertEqual(state, 'all_ok')
        self.assertIn('opencode-go', sentence)
        # main = proxy, proxy down, opencode-go up -> spare tire, as before
        state, _ = mh.summarize(mh.run(env, opener=opener, main='proxy'))
        self.assertEqual(state, 'spare_tire')

    def test_later_env_file_wins_like_hermes(self):
        with tempfile.TemporaryDirectory() as d:
            first, second, out = Path(d) / 'a.env', Path(d) / 'b.env', Path(d) / 'o.json'
            first.write_text('OPENCODE_GO_API_KEY=GOOD' + chr(10))
            second.write_text('OPENCODE_GO_API_KEY=STALE' + chr(10))
            seen = {}
            original = mh.run
            mh.run = lambda env_map, **kw: seen.update(env_map) or original(env_map, opener=status_opener(500), **kw)
            try:
                mh.main(['--env-file', str(first), '--env-file', str(second), '--out', str(out)])
            finally:
                mh.run = original
            self.assertEqual(seen['OPENCODE_GO_API_KEY'], 'STALE')
            self.assertEqual(json.loads(out.read_text())['env_conflicts'], ['OPENCODE_GO_API_KEY'])

    def test_main_writes_report_and_never_leaks_keys(self):
        with tempfile.TemporaryDirectory() as d:
            env = Path(d) / 'e.env'
            env.write_text(f'GOOGLE_API_KEY={KEY}\n')
            out = Path(d) / 'out.json'
            original = mh.run
            mh.run = lambda env_map, **kw: original(env_map, opener=status_opener(500))
            try:
                code = mh.main(['--env-file', str(env), '--out', str(out)])
            finally:
                mh.run = original
            self.assertEqual(code, 1)
            self.assertNotIn(KEY, out.read_text())


if __name__ == '__main__':
    unittest.main()


class HealthTruthTests(unittest.TestCase):
    def report(self, primary=False, spare=True):
        return {'checked_at':1000,'main':'opencode-go','routes':[
            {'route':'opencode-go','ok':primary},{'route':'proxy','ok':spare}]}

    def test_spare_success_does_not_heal_primary_or_prove_session_route(self):
        view=mh.health_snapshot(self.report(),now=lambda:1100)
        self.assertEqual(view['health_status'],'degraded')
        self.assertEqual(view['preferred_status'],'unavailable')
        self.assertEqual(view['actual_session_route'],'unknown')

    def test_all_down_stale_missing_and_recovery(self):
        self.assertEqual(mh.health_snapshot(self.report(False,False),now=lambda:1100)['health_status'],'unavailable')
        self.assertEqual(mh.health_snapshot(self.report(),now=lambda:2801)['health_status'],'unknown')
        self.assertEqual(mh.health_snapshot({},now=lambda:1100)['health_status'],'unknown')
        self.assertEqual(mh.health_snapshot(self.report(True),now=lambda:1100)['health_status'],'healthy')

    def test_success_time_only_advances_on_success(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'report.json'
            mh.write_report(self.report(True),p)
            failed=self.report(False,False); failed['checked_at']=1200
            mh.write_report(failed,p)
            self.assertEqual(json.loads(p.read_text())['last_success_at']['opencode-go'],1000)
