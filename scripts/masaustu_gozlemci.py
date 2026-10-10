#!/usr/bin/env python3
"""Masaustu isi bagimsiz gozlemcisi.

Amac: "arac calisti" ile "hedef oldu"yu birbirinden AYIRMAK.

Ekran goruntusunu alir, goruntu yetenegi olan yerel beyne okutur ve
yalniz su uc hukumden birini yazar:

    GORDUM    -> beklenen sonuc ekranda gorunuyor
    GORMEDIM  -> beklenen sonuc ekranda YOK
    BELIRSIZ  -> olculemedi (ekran gelmedi, model hatasi, kesik cevap, kararsizlik)

Kural: hicbir hata/kararsizlik durumu "oldu" sayilmaz.

Kullanim:
    python3 masaustu_gozlemci.py "tarayicida example.com acik"
    python3 masaustu_gozlemci.py "<beklenen>" --model gemini-3.8-flash-high
    python3 masaustu_gozlemci.py "<beklenen>" --gorev-id <kopru gorev id>
    python3 masaustu_gozlemci.py "<beklenen>" --ekran /yol/hazir.png

Cikis kodu: 0 = GORDUM | 1 = GORMEDIM | 2 = BELIRSIZ

OLCULEN TUZAK (09.10.2026): yerel beyn `max_tokens=200` verilince cevabi
~56 karakterde kesiyor (finish_reason=length) -> "GORMEDIM" kayda "GORMED"
geciyor ve hukum taninmiyor. Cozum: max_tokens=1200 ve kesik cevapta BELIRSIZ.

Gizlilik: ekran goruntusu ve ham model cevabi ~/.hermes/ozel/ (700) altinda
tutulur. Kayda yalniz hüküm + gerekce gecer; gerekcede kisisel ayrinti olmamali.
"""
import argparse
import base64
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request

SKILL_SCRIPTS = "/home/hermes/.hermes/skills/system/pablo-execution/scripts"
OZEL = pathlib.Path("/home/hermes/.hermes/ozel")
KAYIT = OZEL / "gozlem.jsonl"
HAM = OZEL / "ham"
BEYIN = "http://127.0.0.1:8999/v1/chat/completions"
BEYIN_ANAHTAR = "antigravity"
VARSAYILAN_MODEL = "claude-3-5-sonnet-latest"
MAX_TOKENS = 1200  # 200 kesiyordu: OLCULDU

ISTEK = """Az once bir masaustu isi istendi. Beklenen sonuc: "{beklenen}"

Ekranda bu sonucun gerceklestigini gosteren bir sey var mi?

CIKTI FORMATI (aynen uygula):
GORDUM
<tek cumle gerekce>

ya da

GORMEDIM
<tek cumle gerekce>

ya da

BELIRSIZ
<tek cumle gerekce>

KURALLAR:
- Ilk satir YALNIZ GORDUM, GORMEDIM veya BELIRSIZ olsun. Baska kelime yazma.
- Gerekcede ekranda NE oldugunu ANLATMA. Program adi, kisi adi, sekme, sohbet,
  haber, mac, kanal, sayfa icerigi YAZMA. Yalniz beklenen seyin gorunup
  gorunmedigini soyle; ornek: "Beklenen pencere ekranda gorunmuyor."
- Emin degilsen BELIRSIZ yaz. Tahmin etme, iyi niyetle doldurma."""


def ekran_al(hedef: pathlib.Path, sure: int = 120) -> tuple:
    """Pablo'dan ekran goruntusu al. (basarili, aciklama)"""
    komut = [sys.executable, os.path.join(SKILL_SCRIPTS, "pablo_shot.py"), str(hedef)]
    cikti = ""
    try:
        s = subprocess.run(komut, capture_output=True, text=True, timeout=sure)
        cikti = ((s.stdout or "") + (s.stderr or "")).strip()
    except subprocess.TimeoutExpired:
        return False, "ekran alma zaman asimi"
    except Exception as e:
        return False, "ekran alma hatasi: %s" % type(e).__name__
    if not hedef.exists() or hedef.stat().st_size < 1000:
        son = cikti.splitlines()[-1][:120] if cikti else "cikti yok"
        return False, "ekran goruntusu gelmedi (%s)" % son
    return True, "ekran alindi (%d bayt)" % hedef.stat().st_size


def _tr_buyuk(metin: str) -> str:
    """Turkce harfleri sadelestirip buyutur: GÖRDÜM -> GORDUM"""
    for a, b in (("İ", "I"), ("ı", "i"), ("Ş", "S"), ("ş", "s"), ("Ğ", "G"), ("ğ", "g"),
                 ("Ü", "U"), ("ü", "u"), ("Ö", "O"), ("ö", "o"), ("Ç", "C"), ("ç", "c")):
        metin = metin.replace(a, b)
    return metin.upper()


def huküm_coz(metin: str) -> tuple:
    """Yalniz tam, tek hukumlu iki satir kabul edilir; sozcuk aramasi kanit degildir."""
    if not isinstance(metin, str) or len(metin) > 2048:
        return "BELIRSIZ", "model cevabi gecersiz"
    satirlar = [s.strip() for s in metin.splitlines() if s.strip()]
    if len(satirlar) != 2:
        return "BELIRSIZ", "model hukum bicimine uymadi"
    hukum, gerekce = _tr_buyuk(satirlar[0]), satirlar[1]
    izinli = ("GORDUM", "GORMEDIM", "BELIRSIZ")
    if (hukum not in izinli or gerekce in ("-", "...") or len(gerekce) > 200
            or any(ad in _tr_buyuk(gerekce) for ad in izinli)):
        return "BELIRSIZ", "model hukum bicimine uymadi"
    return hukum, gerekce


def huküm_ver(beklenen: str, png: pathlib.Path, model: str) -> tuple:
    """(hukum, gerekce, ham_cevap)"""
    try:
        b64 = base64.b64encode(png.read_bytes()).decode()
    except Exception as e:
        return "BELIRSIZ", "goruntu okunamadi: %s" % type(e).__name__, ""
    govde = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": ISTEK.format(beklenen=beklenen)},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
        ]}],
        "max_tokens": MAX_TOKENS,
    }
    try:
        req = urllib.request.Request(
            BEYIN, data=json.dumps(govde).encode(),
            headers={"Authorization": "Bearer " + BEYIN_ANAHTAR, "Content-Type": "application/json"})
        yanit = json.load(urllib.request.urlopen(req, timeout=180))
        secim = yanit["choices"][0]
        metin = (secim["message"].get("content") or "").strip()
        bitis = secim.get("finish_reason")
    except Exception as e:
        return "BELIRSIZ", "beyin hatasi: %s" % type(e).__name__, ""
    if bitis == "length":
        return "BELIRSIZ", "cevap kesildi (finish_reason=length)", metin
    if bitis != "stop":
        return "BELIRSIZ", "cevabin tamamlandigi dogrulanamadi", metin
    hukum, gerekce = huküm_coz(metin)
    return hukum, gerekce, metin


def _gizli_yaz(yol: pathlib.Path, icerik: str) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(yol.parent, 0o700)
    yol.write_text(icerik, encoding="utf-8")
    os.chmod(yol, 0o600)


def kaydet(blok: dict) -> None:
    OZEL.mkdir(parents=True, exist_ok=True)
    os.chmod(OZEL, 0o700)
    with open(KAYIT, "a", encoding="utf-8") as f:
        f.write(json.dumps(blok, ensure_ascii=False) + "\n")
    os.chmod(KAYIT, 0o600)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("beklenen", help="ekranda gorunmesi beklenen sonuc")
    ap.add_argument("--model", default=VARSAYILAN_MODEL)
    ap.add_argument("--gorev-id", default=None)
    ap.add_argument("--ekran", default=None, help="hazir PNG kullan (ekran alma adimini atla)")
    ap.add_argument("--ham-goster", action="store_true", help="ham model cevabini ekrana bas")
    a = ap.parse_args()

    OZEL.mkdir(parents=True, exist_ok=True)
    os.chmod(OZEL, 0o700)
    zaman = time.strftime("%Y-%m-%dT%H:%M:%S")

    png = pathlib.Path(a.ekran) if a.ekran else OZEL / ("gozlem-%s.png" % time.strftime("%Y%m%d-%H%M%S"))
    if a.ekran:
        basarili, aciklama = png.exists(), "hazir goruntu kullanildi"
    else:
        basarili, aciklama = ekran_al(png)
    if basarili:
        os.chmod(png, 0o600)

    ham = ""
    if not basarili:
        hukum, gerekce = "BELIRSIZ", aciklama
    else:
        hukum, gerekce, ham = huküm_ver(a.beklenen, png, a.model)

    if ham:
        _gizli_yaz(HAM / (png.stem + ".txt"), ham)
        if a.ham_goster:
            print("--- ham cevap ---")
            print(ham[:600])

    kaydet({"zaman": zaman, "beklenen": a.beklenen, "hukum": hukum, "gerekce": gerekce,
            "gorev_id": a.gorev_id, "model": a.model,
            "ekran": str(png) if basarili else None})

    print("%s | beklenen: %s" % (hukum, a.beklenen))
    print("gerekce: %s" % gerekce)
    if basarili:
        print("ekran: %s (ozel klasor)" % png.name)
    return {"GORDUM": 0, "GORMEDIM": 1}.get(hukum, 2)


if __name__ == "__main__":
    sys.exit(main())
