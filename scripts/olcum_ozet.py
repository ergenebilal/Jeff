"""Haftalık ölçüm özeti — eylem→sonuç (FIKIR-0002 dar kapsam: satış hunisi).

Salt okunur. cgos.db'yi yalnız okur, tek markdown dosyası yazar. Mesaj GÖNDERMEZ.
Gerçek sonuç YALNIZ olaylardan sayılır (Yanıt geldi / Görüşme / Pilot / Teklif / Tahsilat / Hayır);
aşama (stage) alanındaki eski 'Yanıt geldi' kayıtları 17.10 site-sohbet testleridir ve sayılmaz.

Kullanım:
  python3 olcum_ozet.py [--db /yol/cgos.db] [--out /yol/olcum_ozet.md]
"""
import argparse
import os
import sqlite3
import time
from datetime import datetime, timedelta

GONDERIM = {"WhatsApp'tan yazıldı", "Instagram'dan yazıldı", "E-posta gönderildi",
            "E-posta otopilotu gönderdi", "Elle gönderildi", "Gönder düğmesine bastınız"}
SONUC = {"Yanıt geldi", "Aşama elle değiştirildi: Görüşme", "Pilot kabul edildi",
         "Teklif verildi", "Tahsilat", "Aşama elle değiştirildi: Kapandı"}


def tl(detail):
    import re
    m = re.search(r"(\d+)\s*TL", detail or "")
    return int(m.group(1)) if m else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.environ.get(
        "CGOS_DATA", os.path.expanduser("~/cybergeneos-data")) + "/cgos.db")
    ap.add_argument("--out", default=os.path.expanduser("~/logs/olcum_ozet.md"))
    a = ap.parse_args()

    c = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
    c.row_factory = sqlite3.Row
    simdi = int(time.time())

    leads = {r["id"]: r for r in c.execute("SELECT id,name,stage,channel,last_touch FROM leads")}
    ev = [dict(r) for r in c.execute("SELECT lead_id,ts,title,detail FROM events ORDER BY ts, id")]

    ilk_temas, ilk_sonuc, sonuc_tur = {}, {}, {}
    for e in ev:
        lid = e["lead_id"]
        if lid not in leads:
            continue
        if e["title"] in GONDERIM:
            ilk_temas.setdefault(lid, e["ts"])
        elif e["title"] in SONUC:
            if lid not in ilk_sonuc:
                ilk_sonuc[lid] = e["ts"]
                sonuc_tur[lid] = e["title"]

    temas = set(ilk_temas)
    # eşleştir: sonuç, temasdan SONRA mı?
    sonuclu = {l for l in temas if l in ilk_sonuc and ilk_sonuc[l] > ilk_temas[l]}
    s7 = {l for l in sonuclu if ilk_sonuc[l] - ilk_temas[l] <= 7 * 86400}
    s14 = {l for l in sonuclu if ilk_sonuc[l] - ilk_temas[l] <= 14 * 86400}
    olculemeyen = sorted(
        ((ilk_temas[l], l) for l in temas
         if l not in sonuclu and simdi - ilk_temas[l] >= 14 * 86400),
        key=lambda x: x[0])

    def say(bas):
        return sum(1 for e in ev if e["title"] in bas)
    gorusme = sum(1 for e in ev if e["title"] == "Aşama elle değiştirildi: Görüşme")
    pilot = sum(1 for e in ev if e["title"] == "Pilot kabul edildi")
    teklif = sum(1 for e in ev if e["title"] == "Teklif verildi")
    tahsilat_tl = sum(tl(e["detail"]) for e in ev if e["title"] == "Tahsilat")

    def pct(n, d):
        return "%%%d (%d/%d)" % (round(100 * n / d), n, d) if d else "ölçülmedi (payda 0)"

    L = []
    L.append("# Haftalık Ölçüm Özeti — %s" % datetime.now().strftime("%d.%m.%Y"))
    L.append("")
    L.append("> Kaynak: `cgos.db` (salt okunur). Sonuçlar yalnız **olay** kaydından sayılır; eski "
             "aşama-tabanlı 'Yanıt geldi' kayıtları (17.10 site testleri) sayılmaz.")
    L.append("")
    L.append("## 1) Huni (başlangıçtan beri)")
    L.append("- Temas edilen aday: **%d**" % len(temas))
    L.append("- Görüşme kaydı: **%d**" % gorusme)
    L.append("- Pilot 'evet': **%d**" % pilot)
    L.append("- Teklif verilen: **%d**" % teklif)
    L.append("- Tahsilat: **%d TL**" % tahsilat_tl)
    L.append("")
    L.append("## 2) Eylem → Sonuç (trace_id vekili)")
    L.append("- Temas edilen: **%d**" % len(temas))
    L.append("- 7 gün içinde sonuç: **%s**" % pct(len(s7), len(temas)))
    L.append("- 14 gün içinde sonuç: **%s**" % pct(len(s14), len(temas)))
    L.append("- **14 gündür sonuç yok (ölçülmedi kuyruğu): %d**" % len(olculemeyen))
    L.append("")
    L.append("## 3) 14 gündür sonuçsuz adaylar (en eski %d)" % min(30, len(olculemeyen)))
    if not olculemeyen:
        L.append("- yok")
    for ts, lid in olculemeyen[:30]:
        l = leads[lid]
        gun = int((simdi - ts) / 86400)
        L.append("- %s — gönderim %s, %d gün, kanal: %s" % (
            l["name"], datetime.fromtimestamp(ts).strftime("%d.%m.%Y"), gun, l["channel"] or "?"))
    L.append("")
    L.append("## 4) Ölçülemeyenler (kör noktalar)")
    L.append("- E-posta teslim / geri dönme (bounce): okuyucu yok → **ölçülmedi**")
    L.append("- WhatsApp yanıtı: Bilal'in elle kaydına bağlı; otomatik yakalanmıyor → **kısmi**")
    L.append("")

    metin = "\n".join(L)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(metin)
    # trend için tek satır geçmiş (üzerine yazılmaz, eklenir)
    gecmis = os.path.join(os.path.dirname(a.out), "olcum_gecmis.md")
    satir = "%s | temas=%d | 7g=%d | 14g=%d | 14g-sonucsuz=%d | tahsilat=%d TL\n" % (
        datetime.now().strftime("%Y-%m-%d"), len(temas), len(s7), len(s14), len(olculemeyen), tahsilat_tl)
    with open(gecmis, "a", encoding="utf-8") as f:
        f.write(satir)
    print(metin)
    print("\nYAZILDI: %s" % a.out)
    print("GECMIS: %s" % gecmis)


if __name__ == "__main__":
    main()
