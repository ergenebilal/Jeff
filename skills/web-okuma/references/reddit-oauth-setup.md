# Reddit Reading — Auth & Rate Limits

## Backend Karşılaştırması

| Özellik | Anonim Atom (Varsayılan) | OAuth App Credential |
|---|---|---|
| **Kurulum** | Yapılandırma gerekmez | 1 dakikalık app kaydı, iki `.env` değeri |
| **Rate Limit** | ~1 request / minute / IP | ~100 requests / minute |
| **Thread Verisi** | Gönderi + üst seviye yorumlar, skor yok | İç içe yorumlar, skorlar, num_comments |
| **Kullanıcı Modu** | Kullanıcı gibi davranmaz | Kullanıcı gibi davranmaz |

## OAuth Yapılandırması (`~/.hermes/.env`)

```env
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
```

## Komutlar

```bash
python3 scripts/reddit.py doctor                                  # hangi backend, rate-limit durumu
python3 scripts/reddit.py sub LocalLLaMA --sort hot --limit 15
python3 scripts/reddit.py search "hermes agent" --sub LocalLLaMA --sort new
python3 scripts/reddit.py thread https://www.reddit.com/r/x/comments/abc123/slug/ --limit 40
python3 scripts/reddit.py user spez --limit 10
python3 scripts/reddit.py --json search "topic"                  # makine-okunabilir
```
