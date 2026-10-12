#!/usr/bin/env python3
"""Sunucudan DOGRUDAN bilgisayara akan tam yedek.

Sunucuda arsiv dosyasi OLUSMAZ: mevcut yedek betiginin (jeff_backup.py) kendi
kaynak kesfi ve tutarli veritabani anlik goruntusu fonksiyonlari kullanilir,
tar cikisi dogrudan aga yazilir.

Kullanim (sunucu tarafi):
    python3 jeff_stream_backup.py --port 7711 --minutes 45

Bilgisayardan cekmek icin (tek satir):
    curl -H "X-Token: <TOKEN>" http://100.80.122.74:7711/stream -o jeff-backup-P128.tar.gz

Test (kucuk ornek, yerel):
    python3 jeff_stream_backup.py --test
"""
import argparse
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import time
import secrets
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, '/home/hermes/scripts')
import jeff_backup as jb  # noqa: E402  (ayni kaynak listesi, ayni db anlik goruntusu)

HOME = Path('/home/hermes')
TOKEN = None
STARTED = 0.0
DEADLINE = 0.0
USED = False
LOG = None


def log(msg):
    line = time.strftime('[%H:%M:%S] ') + str(msg)
    print(line, flush=True)
    if LOG:
        try:
            with open(LOG, 'a', encoding='utf-8') as fh:
                fh.write(line + '\n')
        except OSError:
            pass


def build_stream(wfile, test_mode=False, log_fn=log):
    """tar.gz akisini dogrudan sokete yaz. Diske arsiv yazilmaz."""
    work = Path(tempfile.mkdtemp(prefix='stream-work-', dir='/home/hermes/.hermes/cache/scratch'))
    os.chmod(work, 0o700)
    errors = []
    try:
        core = jb.core_sources(HOME)                       # eksik cekirdek kaynak varsa burada patlar
        log_fn('cekirdek kaynak listesi alindi: %d dosya' % len(core))

        if test_mode:
            # TEST: veritabani anlik goruntusu ALINMAZ (diskte yer tutmamasi icin)
            dbs, copied, errors = [], {}, []
            log_fn('TEST MODU: veritabani anlik goruntusu atlandi')
        else:
            dbs = jb.find_databases(HOME)
            copied, errors = jb.snapshot_databases(dbs, work, log_fn)   # tutarli db anlik goruntusu (kucuk)
            log_fn('veritabani anlik goruntusu: %d adet' % len(copied))

        # 'w|gz' = akis modu: geri sarma yok, diske yazmaz
        tar = tarfile.open(fileobj=wfile, mode='w|gz', compresslevel=3)
        try:
            if not test_mode:
                tar.add(work / 'db', arcname='db')

            data = json.dumps(core, indent=1).encode('utf-8')
            info = tarfile.TarInfo('etc/CORE-SOURCES.json')
            info.size, info.mtime, info.mode = len(data), int(time.time()), 0o600
            tar.addfile(info, io.BytesIO(data))

            etc_manifest = {}
            for extra in jb.etc_files():
                if not Path(extra).is_file():
                    continue
                if jb.add_system_file(tar, extra, time.time, log_fn):
                    etc_manifest[jb.etc_arcname(extra)[len('etc/'):]] = str(extra)
            mb = json.dumps(etc_manifest, indent=1).encode('utf-8')
            info = tarfile.TarInfo('etc/MANIFEST.json')
            info.size, info.mtime, info.mode = len(mb), int(time.time()), 0o600
            tar.addfile(info, io.BytesIO(mb))

            for name, text in jb.package_inventory(HOME).items():
                d = text.encode('utf-8')
                info = tarfile.TarInfo(name)
                info.size, info.mtime, info.mode = len(d), int(time.time()), 0o600
                tar.addfile(info, io.BytesIO(d))

            roots = jb.trees(HOME)
            if test_mode:
                roots = [HOME / 'jeff-beyin']
                log_fn('TEST MODU: yalnizca jeff-beyin agaci')
            dbset = {str(p) for p in dbs}
            files = 0
            for root in roots:
                files += jb.add_tree(tar, root, dbset, log_fn)
                log_fn('agac eklendi: %s (toplam %d dosya)' % (root.name, files))
        finally:
            tar.close()
        log_fn('AKIS TAMAM: %d dosya, %d hata' % (files, len(errors)))
        return 0 if not errors else 3
    finally:
        shutil.rmtree(work, ignore_errors=True)


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'          # icerik uzunlugu bilinmiyor -> baglanti kapanisiyla biter
    server_version = 'jeff-stream/1.0'

    def log_message(self, format, *args):   # noqa: A002  (taban sinifin imzasi)
        log('istek: ' + (format % args))

    def do_GET(self):
        global USED
        if self.path == '/health':
            body = b'{"ok":true}\n'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path != '/stream':
            self.send_error(404, 'yol yok')
            return

        if TOKEN and self.headers.get('X-Token') != TOKEN:
            log('REDDEDILDI: jeton hatali (%s)' % (self.client_address[0],))
            self.send_error(403, 'jeton hatali')
            return

        now = time.time()
        if USED:
            log('REDDEDILDI: bu pencere zaten kullanildi')
            self.send_error(410, 'tek kullanimlik pencere kullanildi')
            return
        if now > DEADLINE:
            log('REDDEDILDI: sure doldu')
            self.send_error(410, 'sure doldu')
            return

        USED = True
        log('AKIS BASLIYOR -> %s (uc: %s)' % (self.client_address[0], self.path))
        self.send_response(200)
        self.send_header('Content-Type', 'application/gzip')
        self.send_header('Content-Disposition', 'attachment; filename="jeff-backup.tar.gz"')
        self.end_headers()
        t0 = time.time()
        try:
            rc = build_stream(self.wfile)
        except (BrokenPipeError, ConnectionResetError) as exc:
            log('BAGLANTI KOPTU: %s' % type(exc).__name__)
            return
        except Exception as exc:                       # noqa: BLE001
            log('HATA: %s: %s' % (type(exc).__name__, exc))
            return
        log('AKIS BITTI rc=%s, sure %.1f sn' % (rc, time.time() - t0))
        self.close_connection = True


def main(argv=None):
    global TOKEN, STARTED, DEADLINE, LOG
    ap = argparse.ArgumentParser()
    ap.add_argument('--bind', default='100.80.122.74')
    ap.add_argument('--port', type=int, default=7711)
    ap.add_argument('--minutes', type=int, default=45)
    ap.add_argument('--token', default=None)
    ap.add_argument('--test', action='store_true', help='yerel kucuk ornek akis (sunucu acmaz)')
    ap.add_argument('--log', default='/home/hermes/.hermes/cache/scratch/stream-backup.log')
    a = ap.parse_args(argv)

    LOG = a.log
    TOKEN = a.token or secrets.token_urlsafe(24)
    STARTED = time.time()
    DEADLINE = STARTED + a.minutes * 60

    if a.test:
        out = Path('/home/hermes/.hermes/cache/scratch/stream-test.tar.gz')
        with open(out, 'wb') as fh:
            build_stream(fh, test_mode=True)
        size = out.stat().st_size
        ok = False
        try:
            with tarfile.open(out, 'r:gz') as t:
                names = t.getnames()
                ok = any(n.startswith('etc/') for n in names) and len(names) > 3
        except tarfile.TarError as exc:
            log('TEST: arsiv okunamadi (%s)' % exc)
        log('TEST SONUC: %d bayt, gecerli tar: %s' % (size, ok))
        return 0 if (ok and size > 1000) else 1

    log('AKIS PENCERESI ACIK  %s:%d  (%.0f dakika, tek kullanim)' % (a.bind, a.port, a.minutes))
    log('JETON: %s' % TOKEN)
    srv = ThreadingHTTPServer((a.bind, a.port), Handler)
    srv.daemon_threads = True
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
        log('pencere kapatildi')
    return 0


if __name__ == '__main__':
    sys.exit(main())
