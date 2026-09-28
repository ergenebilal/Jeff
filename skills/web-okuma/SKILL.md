---
name: web-okuma
description: "RSS, Atom, Feed ve Reddit okuma — tarayici gerekmez."
---

# Web Okuma

Sunucudan web icerigi okuma yetenekleri. Tarayici, login veya cookie gerektirmez.

## Kullanım Alanları

- "r/LocalLLaMA ne diyor", "bu Reddit konusunu ozetle" → Reddit
- "bu blogun son yazisi ne", "bu sitenin RSS feedi var mi" → RSS/Atom/JSON Feed
- "GitHub'da yeni release var mi" → RSS (releases.atom)
- Cron job ile periyodik icerik takibi → RSS (daha ucuz ve stabil)

## 1. Reddit Okuma (`scripts/reddit.py`)

Reddit icerikleri: subreddit listeleri, arama, tam konu + yorumlar, kullanici sayfalari.

```bash
python3 scripts/reddit.py doctor                                  # hangi backend, rate-limit durumu
python3 scripts/reddit.py sub LocalLLaMA --sort hot --limit 15
python3 scripts/reddit.py search "hermes agent" --sub LocalLLaMA --sort new
python3 scripts/reddit.py thread https://www.reddit.com/r/x/comments/abc123/slug/ --limit 40
python3 scripts/reddit.py user spez --limit 10
python3 scripts/reddit.py --json search "topic"                  # makine-okunabilir
```

**Iki backend (otomatik secilir):**
- **OAuth** (`REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` `.env`'de): ~100 istek/dk, skorlar + ic ice yorumlar
- **Anonim Atom** (varsayilan): ~1 istek/dk, yalniz ust seviye yorumlar, skor yok

**Reddit potfallari:**
- `www.reddit.com/.json`, `api.reddit.com`, `old.reddit.com` → sunucu IP'lerinden 403
- Anonim feed paylasimli throttle: Reddit icin birlestirilmis istek planla
- `limit` tavsiye niteligidir — 5-25 kayit doner
- 429'da proxy/loop ile "duzeltme" — throttle beklemeyle cozulur

## 2. RSS/Atom/JSON Feed Okuma (`scripts/feed.py`)

Herhangi bir RSS 2.0, RSS 1.0/RDF, Atom veya JSON Feed URL'ini oku. Sayfa URL'si verilirse feed'i otomatik kesfed.

```bash
python3 scripts/feed.py read https://hnrss.org/frontpage --limit 10
python3 scripts/feed.py read https://simonwillison.net/            # sayfa URL'si → feed kesfeder
python3 scripts/feed.py read URL --since 2026-09-01 --json          # sadece yeni kayitlar
python3 scripts/feed.py discover https://example.com/               # aday feed URL'leri
```

**Yaygin feed sablonlari:**
- GitHub: `releases.atom`, `commits/BRANCH.atom`, `tags.atom`
- Reddit: `r/NAME/.rss`, `search.rss?q=...`
- YouTube: `feeds/videos.xml?channel_id=UC...`
- Hacker News: `hnrss.org/frontpage`
- Substack/Medium/WordPress/Ghost: `SITE/feed`, `medium.com/feed/@user`

**Feed potfallari:**
- 200 + HTML = sayfa, feed degil → otomatik kesfe duser
- Reddit feed'leri anonim throttle'i paylasir → `reddit-reading` uzerinden zincirle
- Tarih formatlari: RSS `pubDate` (RFC 822) ve Atom (ISO 8601) → ikisi de UTC'ye normalize
- Cloudflare onlu feed'ler 403 verebilir

## Birlikte Kullanım

- Reddit aramasindan bulunan bir konuyu RSS ile takip etmek: `reddit.py search` ile konuyu bul, sonra o subreddit'in `.rss` feed'ini `feed.py` ile periyodik izle
- Kaynak dogrulama: her iki aracin ciktilarinda `url` alanini referans olarak kullan

## İlgili

- `bagimsiz-dogrulama` → delege arastirma raporlarini dogrulama
- `hedef-pazar-arastirmasi` → paralel subagent arastirmasi protokolu
- `medya-dogrulama` → medya icerik dogrulama