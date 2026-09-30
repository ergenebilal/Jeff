#!/usr/bin/env python3
"""Gorseldeki 8 etkinligi takvime aktarilabilir .ics dosyasina cevir."""
import datetime, json, pathlib

# Gorselden birebir okunan kayitlar (GG.AA.YYYY, SS:DD)
KAYITLAR = [
    ("09.10.2026", "15:30", "Program"),
    ("09.10.2026", "16:00", "Bireysel Görüşme"),
    ("23.10.2026", "15:30", "Program"),
    ("06.11.2026", "15:30", "Program"),
    ("20.11.2026", "15:30", "Program"),
    ("04.12.2026", "15:30", "Program"),
    ("18.12.2026", "15:30", "Program"),
    ("18.12.2026", "16:00", "Bireysel Görüşme"),
]

# Tabloda bitis saati yok. Program 15:30 -> 16:00 ayni gun bireysel gorusme geliyor,
# bu yuzden Program 30 dk varsayildi (cakisma olmasin). Degeristik: soylersen duzeltirim.
SURE = {"Program": 30, "Bireysel Görüşme": 60}   # dakika

TZ = """BEGIN:VTIMEZONE
TZID:Europe/Istanbul
BEGIN:STANDARD
DTSTART:19700101T000000
TZOFFSETFROM:+0300
TZOFFSETTO:+0300
TZNAME:+03
END:STANDARD
END:VTIMEZONE"""

satir = ["BEGIN:VCALENDAR", "VERSION:2.0",
         "PRODID:-//CyberGene//Takvim//TR", "CALSCALE:GREGORIAN", TZ]

ozet = []
for tarih, saat, ad in KAYITLAR:
    g, a, y = tarih.split(".")
    s, dk = saat.split(":")
    bas = datetime.datetime(int(y), int(a), int(g), int(s), int(dk))
    bit = bas + datetime.timedelta(minutes=SURE[ad])
    uid = bas.strftime("%Y%m%dT%H%M") + "-" + ad.replace(" ", "").replace("ö", "o").replace("ü", "u").replace("ş", "s").replace("ı", "i").lower() + "@cybergene.co"
    satir += [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART;TZID=Europe/Istanbul:{bas.strftime('%Y%m%dT%H%M%S')}",
        f"DTEND;TZID=Europe/Istanbul:{bit.strftime('%Y%m%dT%H%M%S')}",
        f"SUMMARY:{ad}",
        "BEGIN:VALARM", "TRIGGER:-PT30M", "ACTION:DISPLAY",
        "DESCRIPTION:30 dakika kaldı", "END:VALARM",
        "END:VEVENT",
    ]
    ozet.append((bas, ad, bit))
satir.append("END:VCALENDAR")

# satir katlama (RFC 5545: 75 karakter)
out = []
for ln in satir:
    b = ln.encode("utf-8")
    if len(b) <= 75:
        out.append(ln); continue
    ilk, kalan = b[:75], b[75:]
    parca = [ilk]
    while kalan:
        parca.append(b" " + kalan[:74]); kalan = kalan[74:]
    out.append("\r\n".join(p.decode("utf-8", "ignore") for p in parca))

ics = "\r\n".join(out) + "\r\n"
p1 = pathlib.Path("/home/hermes/raporlar/cybergene-2026-ekim-kasim-aralik.ics")
p1.write_text(ics, encoding="utf-8")

# ileride API ile yazmak icin ham liste
p2 = pathlib.Path("/home/hermes/raporlar/cybergene-takvim-kayitlari.json")
p2.write_text(json.dumps(
    [{"baslik": ad, "baslangic": bas.isoformat(), "bitis": bit.isoformat(),
      "sure_dk": SURE[ad], "tum_gun": False}
     for bas, ad, bit in ozet], ensure_ascii=False, indent=2), encoding="utf-8")

print(f"{len(ozet)} etkinlik yazildi\n")
print(f"{'BASLANGIC':22s} {'BITIS':8s} ETKINLIK")
for bas, ad, bit in ozet:
    print(f"{bas.strftime('%d.%m.%Y %H:%M'):22s} {bit.strftime('%H:%M'):8s} {ad}")
print(f"\n.ics  -> {p1}")
print(f"json  -> {p2}")
