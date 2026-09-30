#!/usr/bin/env python3
"""
Ön görüşme formu -> yapılandırılmış veri -> dijital çalışan (ajan) tasarım taslağı.

Girdi : formun ürettiği özet metni (info@cybergene.co kutusuna düşen metin)
Çıktı : 1) yapılandırılmış JSON  2) iç ekip için tasarım brief'i
        3) müşteriye gösterilecek sade özet

Kullanım:
    python3 form_to_agent.py --file ozet.txt
    python3 form_to_agent.py --file ozet.txt --json
    cat ozet.txt | python3 form_to_agent.py
"""
import argparse, json, re, sys
from pathlib import Path

HEADER = "CYBERGENE ÖN GÖRÜŞME FORMU"

# Alan etiketleri -> anahtar (formdaki sırayla)
LABELS = [
    ("Firma / kişi",                "firma"),
    ("İlgili kişi",                 "yetkili"),
    ("İletişim",                    "iletisim"),
    ("Sektör",                      "sektor"),
    ("Ekip büyüklüğü",              "ekip"),
    ("Web / Instagram",             "web"),
    ("Çalışma saatleri",            "saat"),
    ("Destek istenen konular",      "is_secim"),
    ("En çok yoran iş",             "is_ana"),
    ("Son yaşanan örnek",           "is_son"),
    ("Sıklık",                      "sik"),
    ("Süre",                        "sure"),
    ("Şu an yapan",                 "kim"),
    ("Aksarsa ne oluyor",           "kayip"),
    ("Bugünkü adımlar",             "adimlar"),
    ("Kullanılan araçlar",          "araclar"),
    ("Program adları",              "arac_ad"),
    ("Bilgilerin durduğu yer",      "nerede"),
    ("Müşteri kanalları",           "kanal"),
    ("Günlük mesaj",                "hacim"),
    ("Sık sorulanlar ve cevapları", "sorular"),
    ("Sizde kalacak kararlar",      "karar"),
    ("Kesinlikle yapmayacaklar",    "yasak"),
    ("Konuşma tarzı",               "ton"),
    ("Diller",                      "dil"),
    ("Fiyat sorulursa",             "fiyat"),
    ("Acil / kızgın müşteri",       "acil"),
    ("Mesai dışı",                  "mesai"),
    ("Hassas bilgi",                "hassas"),
    ("Başarı ölçütü",               "basari"),
    ("Bildirim yolu",               "bildirim"),
    ("Özet saati",                  "zaman"),
    ("Başlangıç isteği",            "baslangic"),
    ("Karar veren",                 "karar_veren"),
    ("Örnek yazışmalar",            "ornek"),
    ("Sorusu",                      "soru"),
]

# Tasarımda kritik alanlar (eksikse uyarı)
CRITICAL = ["firma", "sektor", "is_ana", "is_son", "adimlar", "karar", "yasak", "basari"]


def parse(text: str) -> dict:
    """Özet metnini alanlara ayır."""
    # onay satırı ve sonrası tasarım girdisi değil
    text = re.split(r"\n\s*Onay:", text)[0]
    out = {"_ham": text.strip()}
    m = re.search(r"Doldurma tarihi:\s*(.+)", text)
    out["_tarih"] = m.group(1).strip() if m else ""

    # etiket konumlarını bul: (etiket başlangıcı, değer başlangıcı)
    pos = []
    for label, key in LABELS:
        pat = re.compile(rf"^[ \t]*{re.escape(label)}[ \t]*:[ \t]*(.*)$", re.M)
        for mm in pat.finditer(text):
            pos.append((mm.start(), mm.start(1), label, key))
    pos.sort()

    for i, (lstart, vstart, label, key) in enumerate(pos):
        # değer, BİR SONRAKİ etiketin başlangıcında biter (etiket metni dahil edilmez)
        stop = pos[i + 1][0] if i + 1 < len(pos) else len(text)
        val = text[vstart:stop].strip("\n").rstrip()
        if val.strip():
            out[key] = val
    return out


def bullets(value) -> list:
    """Çok satırlı cevabı madde listesine çevir (var olan tireleri tekrarlamaz)."""
    if not value or not isinstance(value, str):
        return []
    out = []
    for ln in value.splitlines():
        s = ln.strip()
        if not s:
            continue
        s = re.sub(r"^[-•*]\s*", "", s)
        out.append(f"- {s}")
    return out


def findings(d: dict) -> list:
    """Eksik/eksik kalan kritik alanlar."""
    miss = [k for k in CRITICAL if not d.get(k)]
    return [f"«{k}» alanı boş" for k in miss]


def brief(d: dict) -> str:
    """İç ekip için tasarım brief'i."""
    g = lambda k: d.get(k, "").strip() or "—"
    L = []
    A = L.append
    A(f"# Dijital Çalışan Tasarım Brief'i")
    A(f"")
    A(f"**İşletme:** {g('firma')}  ")
    A(f"**Sektör:** {g('sektor')}  ")
    A(f"**Yetkili:** {g('yetkili')} · {g('iletisim')}  ")
    A(f"**Ekip / kanal:** {g('ekip')} · {', '.join(x[2:] for x in bullets(d.get('kanal'))) or '—'}  ")
    A(f"**Günlük mesaj hacmi:** {g('hacim')}  ")
    A(f"**Başlangıç isteği:** {g('baslangic')} · **Karar veren:** {g('karar_veren')}  ")
    A(f"**Form tarihi:** {g('_tarih')}")
    A("")
    A("---")
    A("")
    A("## 1. Üstleneceği iş")
    A(f"**Sorun (kendi ağzından):** {g('is_ana')}")
    A("")
    A(f"**Son yaşanan örnek:**")
    for ln in bullets(d.get("is_son")) or ["—"]:
        A(f"> {ln[2:]}")
    A("")
    A(f"- Sıklık: {g('sik')}")
    A(f"- Bir seferde geçen süre: {g('sure')}")
    A(f"- Şu an yapan: {g('kim')}")
    A(f"- Aksarsa: {g('kayip')}")
    A(f"- Talep edilen destek başlıkları: {', '.join(x[2:] for x in bullets(d.get('is_secim'))) or '—'}")
    A("")
    A("## 2. Bugünkü akış (otomatikleştirilecek adımlar)")
    for ln in bullets(d.get("adimlar")) or ["- —"]:
        A(ln)
    A("")
    A(f"- Kullanılan araçlar: {', '.join(x[2:] for x in bullets(d.get('araclar'))) or '—'}")
    A(f"- Program adları: {g('arac_ad')}")
    A(f"- Bilgiler nerede duruyor: {g('nerede')}")
    A("")
    A("## 3. Ses ve davranış")
    A(f"- Ton: {g('ton')}   · Diller: {g('dil')}")
    A(f"- Fiyat sorusu gelince: {g('fiyat')}")
    A(f"- Acil/kızgın müşteri: {g('acil')}")
    A(f"- Mesai dışı: {g('mesai')}")
    A("")
    A("## 4. Kesin sınırlar (asla aşmayacak)")
    A(f"- Sahibinde kalacak kararlar: {', '.join(x[2:] for x in bullets(d.get('karar'))) or '—'}")
    A(f"- Kesinlikle yapmayacakları: {g('yasak')}")
    A(f"- Hassas bilgi içeriyor mu: {g('hassas')}")
    A("")
    A("## 5. Bilgi tabanı (ajana öğretilecek)")
    A("**Sık sorulanlar ve cevapları:**")
    for ln in bullets(d.get("sorular")) or ["- —"]:
        A(f"  {ln}")
    A("")
    if d.get("ornek"):
        A("**Örnek yazışmalar:**")
        for ln in bullets(d.get("ornek")):
            A(f"  {ln}")
        A("")
    A("## 6. Raporlama ve başarı")
    A(f"- Başarı ölçütü: {g('basari')}")
    A(f"- Bildirim yolu: {g('bildirim')}   · Özet saati: {g('zaman')}")
    A("")
    if d.get("soru"):
        A("## 7. Müşterinin kendi sorusu")
        A(f"> {g('soru')}")
        A("")
    f = findings(d)
    if f:
        A("## ⚠ Eksik bilgi — görüşmede netleştirilecek")
        for x in f:
            A(f"- {x}")
        A("")
    A("---")
    A("_Bu taslak form cevaplarından otomatik üretildi; müşteriye gitmeden önce ekip gözden geçirmelidir._")
    return "\n".join(L)


def client_summary(d: dict) -> str:
    """Müşteriye gösterilecek sade özet (iç kod adı geçmez)."""
    g = lambda k: d.get(k, "").strip() or "—"
    L = []
    A = L.append
    A(f"Merhaba {g('yetkili').split()[0] if g('yetkili') != '—' else ''},".strip().rstrip(",") + ",")
    A("")
    A(f"Formunuzu okuduk. {g('sektor')} işinizde en çok zorlandığınız nokta şu:")
    A("")
    A(f"> {g('is_ana')}")
    A("")
    A("Anlattıklarınıza göre, dijital çalışanınızın şunları üstlenmesini öneriyoruz:")
    for ln in bullets(d.get("is_secim")) or ["- —"]:
        A(ln)
    A("")
    A("Çalışma biçimi:")
    _ilk = bullets(d.get("adimlar"))
    A(f"- Bugün elle yapılan adımlar devralınır: {_ilk[0][2:] if _ilk else '—'}")
    A(f"- Sizinle aynı kanallarda çalışır: {', '.join(x[2:] for x in bullets(d.get('kanal'))) or '—'}")
    A(f"- Sorularınıza sizin sesinizle cevap verir: {g('ton')}")
    A("")
    A("Sizde kalacak kararlar (dijital çalışan bunlara dokunmaz):")
    for ln in bullets(d.get("karar")) or ["- —"]:
        A(ln)
    A("")
    A(f"Başarıyı şöyle ölçeceğiz: {g('basari')}")
    A("")
    A("Bir sonraki adım: bu taslağı birlikte gözden geçirip küçük bir kapsamla başlıyoruz.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--client", action="store_true", help="müşteri özetini de yaz")
    a = ap.parse_args()

    text = Path(a.file).read_text(encoding="utf-8") if a.file else sys.stdin.read()
    if HEADER.lower() not in text.lower():
        print("UYARI: metin ön görüşme formu başlığı içermiyor.\n", file=sys.stderr)

    d = parse(text)
    filled = len([k for k in d if not k.startswith("_")])
    print(f"[ayrıştırıldı] {filled}/{len(LABELS)} alan\n", file=sys.stderr)

    if a.json:
        print(json.dumps(d, ensure_ascii=False, indent=2)); return
    print(brief(d))
    if a.client:
        print("\n\n" + "=" * 60)
        print("MÜŞTERİYE GİDECEK ÖZET")
        print("=" * 60 + "\n")
        print(client_summary(d))


if __name__ == "__main__":
    main()
