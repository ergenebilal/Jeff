# Kapı dosyası üretici — kod iskeleti

Hedef havuzu → canlı denetim → hedef başına dosya + `GUN-PLANI.md` + telefon için CSV.
Toplu denetim tek script'te yapılır; her istek 8-12 sn timeout ile, aralarda ~0.4 sn bekleme.

```python
import re, json, socket, ssl, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
RAKIP_PLATFORMLAR = ["doktortakvimi", "doktorsitesi", "doctoralia"]   # dizin/platform alan adları

def get(u, t=12):
    try:
        d = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
        return d.decode("utf-8", "ignore")
    except Exception as e:
        return f"__HATA__ {type(e).__name__}: {str(e)[:60]}"

def ssl_durum(host):
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=8) as s, \
             ctx.wrap_socket(s, server_hostname=host) as ss:
            c = ss.getpeercert()
            return "geçerli", dict(x[0] for x in c["subject"]).get("commonName", "?")
    except Exception as e:
        return f"geçersiz ({type(e).__name__})", "-"

def site_denetle(url):
    bulgu = []
    host = re.sub(r"^https?://", "", url).split("/")[0]
    rakip = [r for r in RAKIP_PLATFORMLAR if r in host.lower()]
    if rakip:
        bulgu.append(f"KENDİ SİTESİ YOK — adres bir platform sayfası ({rakip[0]})")
    h = get(url)
    if h.startswith("__HATA__"):
        return bulgu + ["site açılmıyor: " + h.replace("__HATA__ ", "")], {}
    if 'href="tel:' not in h.lower():            bulgu.append("telefon tıklanabilir DEĞİL")
    if not re.search(r'name=["\']viewport', h, re.I): bulgu.append("mobil uyum YOK")
    if "wa.me" not in h and "whatsapp" not in h.lower(): bulgu.append("WhatsApp bağlantısı YOK")
    if not re.search(r"gtag|googletagmanager|analytics\.js", h, re.I): bulgu.append("ölçüm YOK")
    ig = [i for i in dict.fromkeys(re.findall(r"instagram\.com/([A-Za-z0-9_.]{3,30})", h))
          if i.lower() not in ("p", "reel", "explore", "accounts")]
    if not ig: bulgu.append("sitede Instagram bağlantısı yok")
    return bulgu, {"host": host, "boyut_kb": len(h) // 1024, "instagram": ig[:2]}

def platform_kaydi(ad):
    """Satılan platformda bu işletmenin kaydı var mı (platformun kendi arama yolu)."""
    h = get("https://<platform>/?s=" + urllib.parse.quote(ad), t=15)
    if h.startswith("__HATA__"):
        return None
    return len(set(re.findall(r"/doktor/([a-z0-9-]+)", h)))   # profil link sayısı
```

## Kapıda ilk cümle türetimi
Bulguları öncelik sırasına diz, **ilk vurucu olanı** cümleye çevir:
1. rakip platform sayfası / site yok → "hasta aradığında gidecek kendi sayfanız yok"
2. telefon tıklanmıyor → "numaraya basıp arayamıyorlar, arayan kayboluyor"
3. ölçüm yok → "kaç kişinin geldiği bilinmiyor"
4. WhatsApp yok → "hızlı iletişim kanalı kapalı"
5. hiç bulgu yok → "zemin sağlam; konu görünürlük değil, talebin randevuya dönmesi"

## Rota gruplama
Ham mahalle token'ı ile gruplama yapma. Sabit bölge kovaları tanımla ve adres/mahalle metninde ara:
```python
BOLGELER = [("İhsaniye", ["ihsaniye", "setbaşı", "hocaalizade"]),
            ("Odunluk", ["odunluk", "akpınar"]),
            ("Beşevler", ["beşevler"]),
            ("Esentepe / 29 Ekim", ["esentepe", "29 ekim", "özlüce"]),
            ("Konak / FSM", ["konak", "fsm", "lotus"])]
```
Kovaları büyükten küçüğe **3 güne** dağıt (`i % 3`) → günde 8-12 kapı.

## Alıcı tipi filtresi
Satılan ürün kimeyse liste o tipte kalır. Hekim ilanı için güzellik salonu/kuaför hedefleri ayıkla:
```python
HEKIM_DISI = ("güzellik salonu", "kuaför", "bakım", "tırnak")
hekimler = [h for h in hedefler if not any(k in h["ad"].lower() for k in HEKIM_DISI)]
```
Ayrılanlar dosyada "ayrı tutulanlar" başlığıyla görünür kalsın (yanlışlıkla sahaya çıkmasın).

## Çıktı
- `GUN-PLANI.md` — gün gün rota, her kapı altında tespit + cümle + kayıt kutuları
- `dosya/<no>-<slug>.md` — tek kapı dosyası (telefonda açılacak)
- `hedefler.csv` — hızlı liste (telefon/Notlar uygulamasına aktarılabilir)
