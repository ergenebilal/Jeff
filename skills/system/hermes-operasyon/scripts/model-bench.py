#!/usr/bin/env python3
"""OpenCode Go / Zen (veya herhangi OpenAI-uyumlu uç nokta) model kıyas koşucusu.

Görevler:
  T1 araç çağırma · T2 Türkçe sade anlatım · T3 talimat takibi · T4 uzun bağlam iğnesi
  T5 yazma/boş-cevap ORANI (1200/2500/4000 limitleri, `--repeats N`)
  T6 görsel okuma (`--vision-image <png>`)
  T7 reasoning-parametre uyumu (`--probe-params`)

Kullanım:
  python3 model-bench.py --models glm-5.3-flash deepseek-v4.1-flash --repeats 3
  python3 model-bench.py --models glm-5.3-flash --vision-image /tmp/sayi.png --probe-params
  python3 model-bench.py --key-from-pid 12345 --models mimo-v2.5 --out /tmp/bench.json

Anahtar sırası: --api-key > $OPENCODE_GO_API_KEY > /proc/<pid>/environ.
Anahtar ASLA ekrana yazılmaz.

NOT: uzun bağlam/görsel görevleri saniyeler sürer — bu betiği execute_code hücresinde
uzun sıralı koşturma (300 sn limiti keser); terminal'de veya background ile çalıştır.
"""
import argparse, base64, json, mimetypes, os, sqlite3, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = 'hermes-agent/2.1'
SESSION = 'model-bench'

TOOLS = [{"type": "function", "function": {
    "name": "get_weather", "description": "Hava durumu",
    "parameters": {"type": "object", "properties": {"sehir": {"type": "string"}}, "required": ["sehir"]}}}]

LISTE = ["kırmızı", "mavi", "yeşil", "sarı", "mor", "turuncu",
         "pembe", "kahverengi", "siyah", "beyaz", "gri", "lacivert"]
BEKLENEN = {"sarı", "siyah", "gri"}

T2_SORU = ("Şu cümleyi teknik terim kullanmadan, bir arkadaşına anlatır gibi "
           "1-2 cümleyle TÜRKÇE yaz: 'Reverse proxy arkasındaki TLS sertifikası "
           "14 gün içinde expire olacak.'")

# Uzun çıktı isteyen görev: gizli düşünme bütçesini yakan modeller burada boş döner.
YAZ_SORU = ("Bir veteriner kliniğinin WhatsApp'tan randevu sürecini anlatan, Türkçe, "
            "en az 12 cümlelik bir bilgilendirme metni yaz. Selamlama, adımlar, "
            "dikkat edilmesi gerekenler ve kapanış bölümleri olsun.")
YAZ_LIMITLERI = (1200, 2500, 4000)

PARAM_DENEMELERI = [("reasoning_effort:low", {"reasoning_effort": "low"}),
                    ("reasoning_effort:minimal", {"reasoning_effort": "minimal"}),
                    ("enable_thinking:false", {"enable_thinking": False}),
                    ("thinking:disabled", {"thinking": {"type": "disabled"}})]


def uzun_baglam(n=900):
    dolgu = "\n".join(f"Kayit {i}: referans kodu {1000 + i * 7}, durum 'arsivde'." for i in range(1, n))
    return (f"ONEMLI NOT: odeme esigi 4.871 TL olarak guncellendi.\n{dolgu}\n"
            "SORU: odeme esigi kac TL? Sadece sayiyi yaz.")


def gorevler():
    return {
        "T1_arac": ({"messages": [
            {"role": "system", "content": "Hava durumu sorulunca get_weather aracını çağır."},
            {"role": "user", "content": "Bursa'da hava nasıl? Aracı çağır."}], "tools": TOOLS}, 400),
        "T2_turkce": ({"messages": [{"role": "user", "content": T2_SORU}]}, 900),
        "T3_talimat": ({"messages": [{"role": "user", "content":
            "Şu listeden SADECE 4., 9. ve 11. maddeleri, başlarında tire olacak şekilde, "
            "başka hiçbir şey yazmadan ver:\n" +
            "\n".join(f"{i + 1}. {w}" for i, w in enumerate(LISTE))}]}, 900),
        "T4_uzunbaglam": ({"messages": [{"role": "user", "content": uzun_baglam()}]}, 300),
    }


def anahtar(api_key, pid):
    if api_key:
        return api_key
    if os.environ.get("OPENCODE_GO_API_KEY"):
        return os.environ["OPENCODE_GO_API_KEY"]
    pids = [pid] if pid else []
    if not pid:
        try:
            con = sqlite3.connect(os.path.expanduser("~/.hermes/state.db"))
            pids = [r[0] for r in con.execute("select pid from gateway_heartbeats order by last_heartbeat desc limit 3")]
        except Exception:
            pids = []
    for p in pids:
        try:
            for satir in open(f"/proc/{p}/environ", "rb").read().decode("utf8", "replace").split("\0"):
                if satir.startswith("OPENCODE_GO_API_KEY="):
                    return satir.split("=", 1)[1]
        except Exception:
            continue
    sys.exit("Anahtar bulunamadı: --api-key ver veya OPENCODE_GO_API_KEY tanımla")


def cagir(base, key, model, yuk, mt, timeout):
    govde = {"model": model, "temperature": 0, "max_tokens": mt, **yuk}
    istek = urllib.request.Request(
        base.rstrip("/") + "/chat/completions", data=json.dumps(govde).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                 "User-Agent": UA, "x-opencode-session": SESSION})
    t = time.time()
    try:
        d = json.loads(urllib.request.urlopen(istek, timeout=timeout).read())
        ch = d["choices"][0]
        return {"ok": True, "ms": int((time.time() - t) * 1000), "content": ch["message"].get("content"),
                "tool_calls": ch["message"].get("tool_calls") or [],
                "finish": ch.get("finish_reason"), "usage": d.get("usage", {}),
                "bos": not (ch["message"].get("content") or "").strip()}
    except urllib.error.HTTPError as e:
        return {"ok": False, "code": e.code, "err": e.read().decode("utf8", "replace")[:160]}
    except Exception as e:
        return {"ok": False, "err": type(e).__name__ + ": " + str(e)[:120]}


def kos(args, model):
    sonuc = {"model": model}
    for ad, (yuk, mt) in gorevler().items():
        r = cagir(args.base_url, args.key, model, yuk, mt, args.timeout)
        # Reasoning modelleri küçük limitte content boş + finish=length döner.
        # ÖLÇÜLEN TABAN 4000: 1200'de 3/3, 2500'de 1/3 boş cevap, 4000'de 0.
        if r.get("ok") and r.get("bos") and r.get("finish") == "length" and mt < 4000:
            r2 = cagir(args.base_url, args.key, model, yuk, 4000, args.timeout)
            r2["retry_mt"] = 4000
            r = r2
        sonuc[ad] = r
    if args.repeats > 0:
        sonuc["T5_yazma"] = yazma_kos(args, model)
    if args.vision_image:
        sonuc["T6_vision"] = cagir(args.base_url, args.key, model, vision_yuk(args.vision_image), 300, args.timeout)
    if args.probe_params:
        sonuc["T7_params"] = param_probe(args, model)
    return sonuc


def yazma_kos(args, model):
    """Aynı yazma görevini birden çok çıktı sınırında, `--repeats` kadar koşar.
    Tek koşu kanıt değil; asıl ölçü boş cevap ORANIDIR."""
    cikti = {}
    for mt in YAZ_LIMITLERI:
        kayitlar = []
        for _ in range(max(1, args.repeats)):
            r = cagir(args.base_url, args.key, model,
                      {"messages": [{"role": "user", "content": YAZ_SORU}]}, mt, args.timeout)
            kayitlar.append({"mt": mt, "ok": bool(r.get("ok")), "bos": bool(r.get("ok") and r.get("bos")),
                             "finish": r.get("finish"), "ms": r.get("ms"),
                             "out": (r.get("usage") or {}).get("completion_tokens")})
        cikti[str(mt)] = kayitlar
    return cikti


def vision_yuk(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    return {"messages": [{"role": "user", "content": [
        {"type": "text", "text": "Bu görseldeki sayıyı sadece rakamla yaz."},
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}]}


def param_probe(args, model):
    """Hangi reasoning parametresi kabul ediliyor (400 mü), etkisi ne?"""
    cikti = {}
    for ad, ek in PARAM_DENEMELERI:
        r = cagir(args.base_url, args.key, model,
                  {"messages": [{"role": "user", "content": "Tek kelimeyle 'tamam' yaz."}], **ek},
                  200, args.timeout)
        cikti[ad] = {"durum": "200" if r.get("ok") else str(r.get("code") or "hata"),
                     "ms": r.get("ms"), "icerik": bool((r.get("content") or "").strip())}
    return cikti


def puanla(ad, r):
    if not r.get("ok"):
        return "HATA %s" % (r.get("code") or r.get("err"))
    icerik = (r.get("content") or "")
    if ad == "T1_arac":
        tc = r.get("tool_calls") or []
        if not tc:
            return "arac YOK"
        adlar = [(t.get("function") or {}).get("name") for t in tc]
        return ("OK " + ",".join(a or "?" for a in adlar)) if "get_weather" in adlar else "yanlis arac"
    if ad == "T2_turkce":
        jargon = [w for w in ("TLS", "reverse proxy", "expire", "proxy") if w.lower() in icerik.lower()]
        cjk = sum(1 for ch in icerik if ord(ch) > 0x4E00)  # dil kayması: Çince/Japonca kaçağı
        if cjk > 5:
            return "DIL KAYMASI (%d CJK)" % cjk
        return "OK" if icerik and not jargon else ("jargon:%s" % jargon if icerik else "BOS")
    if ad == "T3_talimat":
        bulunan = {w for w in BEKLENEN if w in icerik}
        fazla = [w for w in LISTE if w not in BEKLENEN and w in icerik]
        return "OK" if bulunan == BEKLENEN and not fazla else "eksik/fazla"
    if ad == "T4_uzunbaglam":
        return "OK" if "4871" in icerik.replace(".", "") else "BULAMADI"
    return "?"


def satir(h):
    p = [h["model"][:24]]
    for ad in ("T1_arac", "T2_turkce", "T3_talimat", "T4_uzunbaglam"):
        p.append(puanla(ad, h.get(ad, {})))
    y = h.get("T5_yazma") or {}
    hepsi = [r for v in y.values() for r in v]
    p.append(("bos %d/%d" % (sum(1 for r in hepsi if r["bos"]), len(hepsi))) if hepsi else "-")
    v = h.get("T6_vision")
    p.append(("gorsel " + ("OK" if v.get("ok") and (v.get("content") or "").strip() else "BOS/HATA")) if v else "-")
    if h.get("T7_params"):
        p.append("param " + " ".join("%s=%s" % (k, x["durum"]) for k, x in h["T7_params"].items()))
    ms = [r.get("ms") for r in h.values() if isinstance(r, dict) and isinstance(r.get("ms"), int)]
    p.append(("%dms" % (sum(ms) // len(ms))) if ms else "-")
    return " | ".join(str(x) for x in p)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="https://opencode.ai/zen/go/v1")
    p.add_argument("--models", nargs="+", required=True)
    p.add_argument("--api-key", default="")
    p.add_argument("--key-from-pid", type=int, default=0)
    p.add_argument("--out", default="/tmp/model-bench.json")
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--repeats", type=int, default=1, help="T5 yazma görevinde limit başına tekrar (boş cevap oranı)")
    p.add_argument("--vision-image", default="", help="T6: içinde okunacak sayı olan PNG yolu")
    p.add_argument("--probe-params", action="store_true", help="T7: reasoning parametre uyumu")
    args = p.parse_args()
    args.key = anahtar(args.api_key, args.key_from_pid)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        hepsi = list(ex.map(lambda m: kos(args, m), args.models))

    json.dump({h["model"]: h for h in hepsi}, open(args.out, "w"), ensure_ascii=False, indent=1)
    print("model | T1 | T2 | T3 | T4 | T5 | T6 | T7 | ort.sure")
    for h in hepsi:
        print(satir(h))
    print(f"\nHam cikti: {args.out}")


if __name__ == "__main__":
    main()
