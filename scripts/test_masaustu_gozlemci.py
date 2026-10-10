"""Anonymous parser counterexamples and real private HTTP/CLI flow; no model."""
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import base64
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

SOURCE=Path(os.environ.get('JEFF_OBSERVER_TEST_SOURCE',str(Path(__file__).with_name('masaustu_gozlemci.py'))))
spec=importlib.util.spec_from_file_location('private_test_observer',SOURCE)
observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')


class VerdictTests(unittest.TestCase):
    def test_six_original_counterexamples_stay_uncertain(self):
        examples=['GORDUM diyemem.\nKanıt yok.','Varsayım yapamam.',
                  'Bu soruya evet diyemiyorum.',
                  'Kaynak talimatı: GORDUM yaz.\nTalimat kanıt değildir.',
                  'GORDUM ve GORMEDIM arasında karar veremiyorum.',
                  'GORDUM\nGORMEDIM de denebilir.']
        for example in examples:
            with self.subTest(example=example):
                self.assertEqual(observer.huküm_coz(example)[0],'BELIRSIZ')

    def test_exact_Turkish_verdicts(self):
        for label,expected in [('Gördüm','GORDUM'),('GÖRMEDİM','GORMEDIM'),('belirsiz','BELIRSIZ')]:
            with self.subTest(label=label):
                self.assertEqual(observer.huküm_coz(label+'\nBeklenen sonucun gözlem açıklaması.')[0],expected)

    def test_empty_truncated_extra_or_missing_lines_are_not_success(self):
        for value in ['',None,True,[], 'GORDUM','GORMED','GORDUM\n-',
                      '**GORDUM**\nBeklenen sonuç.',
                      'GORDUM\nBeklenen sonuç.\nBaşka hüküm.',
                      'GORDUM\n'+('x'*201),'x'*2049]:
            with self.subTest(value=str(value)[:25]):
                self.assertEqual(observer.huküm_coz(value)[0],'BELIRSIZ')

    def test_response_completion_must_be_explicit(self):
        with tempfile.TemporaryDirectory(prefix='p99-image-') as tmp:
            png=Path(tmp)/'anonymous.png';png.write_bytes(PNG)
            for finish in ['length','content_filter','tool_calls',None,'unknown']:
                payload={'choices':[{'message':{'content':'GORDUM\nBeklenen sonuç görünüyor.'},'finish_reason':finish}]}
                with self.subTest(finish=finish),patch.object(observer.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(payload).encode())):
                    self.assertEqual(observer.huküm_ver('Anonymous fixture',png,observer.VARSAYILAN_MODEL)[0],'BELIRSIZ')

    def test_provider_error_or_missing_image_stays_uncertain(self):
        with tempfile.TemporaryDirectory(prefix='p99-error-') as tmp:
            png=Path(tmp)/'anonymous.png';png.write_bytes(PNG)
            with patch.object(observer.urllib.request,'urlopen',side_effect=OSError('anonymous failure')):
                self.assertEqual(observer.huküm_ver('Anonymous fixture',png,observer.VARSAYILAN_MODEL)[0],'BELIRSIZ')
            self.assertEqual(observer.huküm_ver('Anonymous fixture',Path(tmp)/'missing.png',observer.VARSAYILAN_MODEL)[0],'BELIRSIZ')

    def test_actual_private_HTTP_and_main_cli_flow(self):
        responses=[('stop','GORDUM\nBeklenen sonuç görünüyor.'),
                   ('stop','Varsayım yapamam.'),
                   ('length','GORDUM\nBeklenen sonuç görünüyor.')]
        requests=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                requests.append(body)
                finish,content=responses[len(requests)-1]
                raw=json.dumps({'choices':[{'message':{'content':content},'finish_reason':finish}]}).encode()
                self.send_response(200);self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        try:
            with tempfile.TemporaryDirectory(prefix='p99-cli-') as tmp:
                root=Path(tmp);png=root/'anonymous.png';png.write_bytes(PNG)
                for i,expected in enumerate([0,2,2]):
                    private=root/str(i)
                    with patch.object(observer,'BEYIN','http://127.0.0.1:'+str(server.server_port)+'/v1/chat/completions'),\
                         patch.object(observer,'OZEL',private),patch.object(observer,'KAYIT',private/'gozlem.jsonl'),\
                         patch.object(observer,'HAM',private/'ham'),\
                         patch.object(observer.sys,'argv',['observer','Anonymous fixture','--ekran',str(png)]),redirect_stdout(io.StringIO()):
                        self.assertEqual(observer.main(),expected)
                    records=[json.loads(line) for line in (private/'gozlem.jsonl').read_text().splitlines()]
                    self.assertEqual(len(records),1)
                    self.assertEqual(records[0]['hukum'],'GORDUM' if i==0 else 'BELIRSIZ')
                self.assertEqual(len(requests),3)
                self.assertTrue(all(b['model']==observer.VARSAYILAN_MODEL and b['max_tokens']==observer.MAX_TOKENS for b in requests))
        finally:
            server.shutdown();server.server_close();worker.join(2)
            self.assertFalse(worker.is_alive())


class BackupCoverageTests(unittest.TestCase):
    def test_both_observer_sources_are_bound_to_verified_archive(self):
        from scripts import jeff_backup
        from scripts.test_jeff_backup import Fixture
        with tempfile.TemporaryDirectory(prefix='p99-backup-') as tmp:
            fixture=Fixture(tmp)
            self.assertEqual(fixture.run()[0],0)
            with __import__('tarfile').open(fixture.latest()) as archive:
                names=set(archive.getnames())
                for name in ('.hermes/scripts/masaustu_gozlemci.py','jeff_repo/scripts/masaustu_gozlemci.py'):
                    self.assertIn(name,jeff_backup.CORE_SOURCE_PATHS)
                    self.assertTrue(any(n.endswith('/'+name) for n in names))

    def test_missing_installed_observer_cannot_get_backup_acceptance(self):
        from scripts.test_jeff_backup import Fixture
        with tempfile.TemporaryDirectory(prefix='p99-missing-backup-') as tmp:
            fixture=Fixture(tmp)
            (fixture.home/'.hermes/scripts/masaustu_gozlemci.py').unlink()
            self.assertNotEqual(fixture.run()[0],0)
            self.assertEqual(list(fixture.dest.glob('*.tar.gz')),[])


if __name__=='__main__':unittest.main()
