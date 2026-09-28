# Dijital Ayak İzi Temizleme

Kullanıcı şantaj/tehdit/pishing gibi bir durumda kişisel bilgilerinin (telefon, email, adres) internette açıkta olup olmadığını sorguladığında veya "dijital ayak izimi sil" dediğinde bu prosedürü uygula.

## Adım 1: Web Sitesini Durdur

Domain'e bağlı web sitesi varsa container'ı durdur:

```bash
# Container'ları listele
docker ps --format "table {{.Names}}\t{{.Status}}"

# İlgili container'ı durdur
docker stop <container-adı>

# Durduğunu doğrula
curl -s -o /dev/null -w "%{http_code}" -m 3 https://<domain>.com
```

## Adım 2: Site İçeriğinde PII Taraması

Site durdurulsa bile Google cache'de telefon/email/adres olabilir:

```bash
# Google'da domain'i ara (web_search ile)
# Alternatif: web_extract ile siteyi çekip telefon/email pattern'lerini tara
```

**Bulunabilecek PII'ler:**
- Telefon numarası (`+90 5xx xxx xx xx` formatında)
- Email adresleri
- Fiziksel adres
- Sosyal medya linkleri (Instagram, LinkedIn vb.)

## Adım 3: WHOIS Kontrolü

Domain kaydında kişisel bilgiler açıkta olabilir. Kontrol et:

```python
# Python whois (pip install python-whois)
import whois
w = whois.whois('<domain>.com')
print(w.name, w.phone, w.email, w.address)
```

WHOIS bilgileri açıktaysa: domain kayıt şirketinde **WHOIS Privacy / Domain Privacy** aktifleştir. Çoğu registrarda bu ücretsizdir.

## Adım 4: Google Cache Temizliği

Google'da hâlâ eski site içeriği görünüyorsa:
- Google URL Removal Tool: https://search.google.com/search-console/remove
- Site sahibi doğrulaması gerekebilir (DNS TXT kaydı veya HTML dosyası ile)
- Site tamamen kapalıysa ve Google crawl edemiyorsa, cache zamanla kendiliğinden temizlenir (genelde 1-4 hafta)

## Adım 5: Ek Yüzeyler

Kullanıcıya şunları da kontrol etmesini öner:

| Yüzey | Aksiyon |
|-------|---------|
| Instagram | Hesabı gizli yap veya dondur |
| Telegram | Kullanıcı adını değiştir, telefon numarasını "Kimse" yap |
| LinkedIn | Profili gizle |
| GitHub | Kişisel repolarda PII var mı kontrol et |
| WHOIS | Domain privacy aç |

## Önemli Not

Bu prosedür **sadece var olan izleri temizler**. Yeni bir domain alırken her zaman WHOIS privacy'yi aktifleştir. Site içeriğinde asla direkt telefon numarası kullanma — WhatsApp linki veya iletişim formu tercih et.
