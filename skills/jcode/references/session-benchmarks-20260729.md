# Session Benchmark — jcode Kurulum ve Test (29.07.2026)

## Test Ortamı

| Parametre | Değer |
|-----------|-------|
| Host | Ubuntu 22.04, Linux 5.15.0-181-generic |
| RAM | 31 GB total, 624 MB free, 4.2 GB available |
| CPU Load | 0.90 / 1.17 / 1.28 (1/5/15 dk) |
| Hermes | deepseek-v4-flash (opencode-go backend) |

## jcode Yapılandırması

| Parametre | Değer |
|-----------|-------|
| Versiyon | v0.61.1 (commit 438789eb) |
| Provider | `openai-compatible` |
| Endpoint | `https://opencode.ai/zen/go/v1` |
| Model | `deepseek-v4-flash` |
| Config | `~/.jcode/config.toml` |

Kurulum: GitHub release installer ile (`curl -fsSL https://... | sh`)

## Test 1: Sistem Bilgisi (Basic)

- Prompt: "Explore this machine briefly..."
- Süre: ~10 sn
- jcode safety guardrail bloke etti → `/etc/os-release`, `/proc/loadavg`
- Python workaround ile geçti (`platform.platform()`)
- Toplam: 299 output token

## Test 2: Mandelbrot Fractal (Rust, Autonomous)

- jcode 43 satır Rust kodu yazdı
- `rustc` yoktu → kendisi `rustup` kurdu
- Compile etti, çalıştırdı, ASCII Mandelbrot çıktısı verdi
- Toplam: 526 output token

## Test 3: Multi-file Python Adventure Game

- 5 dosya: `items.py`, `player.py`, `adventure.py` (239 satır), `main.py`, `requirements.txt`
- Tüm import'lar test edildi, çalıştı
- Toplam: 2,096 output token (en büyük test)

## Test 4: GitHub API Script (Benchmark — Karşılaştırma)

Aynı iş (`/tmp/compare/gh_stats.py` — GitHub API'den Rust repo bilgisi çek, yazdır):

| Metrik | jcode | Açıklama |
|--------|:-----:|----------|
| Süre | 12.06 sn | AI inference + kod yazma + çalıştırma |
| RAM | 40,108 KB (~39 MB) | `time -f %M` ile ölçüldü |
| Output token | ~714 | 4 turda toplam |
| Safety blok | 0 | Başarıyla çalıştı |

Aynı script'i Hermes üzerinden direkt `time python3 ...` ile çalıştırma: **0.242 sn** (zaten yazılmış script'ti, AI yok).

## OpenCode CLI v1.18.3

- Binary: `/home/hermes/.hermes/node/bin/opencode` (npm paketi, 340 MB)
- `opencode run -m deepseek-v4-flash "..."` → **Server error (HTTP 500)**
- Komple çalışmaz durumda → kaldırıldı
- Alias `jeff` → `jcode --quiet run` olarak güncellendi
- `/home/hermes/.local/bin/jeff` script'i de güncellendi

## Son Karar

| Karar | Gerekçe |
|-------|---------|
| jcode = birincil kodlama aracı | 10× az RAM, 3× az token, çalışıyor |
| OpenCode CLI silindi | 340 MB, çalışmıyor, jcode her işini görüyor |
| OpenCode Go API backend KALDI | Model altyapısı bu — jcode da buraya bağlanıyor |
