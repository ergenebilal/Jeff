# RSS / Atom / JSON Feed Kalıpları ve Hızlı Referans

## Hızlı Referans Tablosu

| Kaynak | Feed URL Deseni |
|---|---|
| GitHub (releases / commits / tags) | `https://github.com/OWNER/REPO/releases.atom`, `.../commits/BRANCH.atom`, `.../tags.atom` |
| Subreddit / Reddit Arama | `https://www.reddit.com/r/NAME/.rss`, `https://www.reddit.com/search.rss?q=...` (1 req/min anon) |
| YouTube kanalı | `https://www.youtube.com/feeds/videos.xml?channel_id=UC...` |
| Hacker News | `https://hnrss.org/frontpage`, `https://hnrss.org/newest?q=TERM` |
| arXiv Kategori | `https://rss.arxiv.org/rss/cs.CL` |
| Substack / Medium / WordPress / Ghost | `SITE/feed`, `medium.com/feed/@user`, `SITE/rss/` |
| Podcasts | Sayfadaki podcast RSS URL'si (`discover` komutu ile kesfedilir) |

## Kullanım Komutları

```bash
python3 scripts/feed.py read https://hnrss.org/frontpage --limit 10
python3 scripts/feed.py read https://simonwillison.net/            # sayfa URL'si → feed kesfeder
python3 scripts/feed.py read URL --since 2026-09-01 --json          # sadece yeni kayitlar
python3 scripts/feed.py discover https://example.com/               # aday feed URL'leri
```

## Potfallar
- **200 + HTML = sayfa, feed degil:** Otomatik kesfe duser.
- **Tarih formatlari:** RSS `pubDate` (RFC 822) ve Atom (ISO 8601) UTC'ye normalize edilir.
- **Cloudflare engeli:** Cloudflare onlu feed'ler 403 verebilir.
