# Cron Optimizasyonu — 10 Ağustos 2026

## Yapılan Değişiklikler

| Aksiyon | Job | Önce | Sonra |
|---------|-----|------|-------|
| 🗑️ Kaldırıldı | `jeff-sabah-brifingi` | v2 legacy (script) | — |
| 🔧 No-agent | `kart-hatirlatma-denizbank` | Agent 🔥 | Script ✅ |
| 🔧 No-agent | `kart-hatirlatma-yk-hepsiburada` | Agent 🔥 | Script ✅ |
| 🔧 No-agent | `kart-hatirlatma-yk-word-eko` | Agent 🔥 | Script ✅ |
| 🔧 No-agent | `jeff3-sabah-brifingi` | Agent 🔥 | Script ✅ |
| 🔧 No-agent | `jeff3-aksam-raporu` | Agent 🔥 | Script ✅ |
| ⏰ Kaydırıldı | `rakip-monitoring` | Pzt 10:00 | Pzt 10:05 |

## Son Durum (16 cron)

- 13 no_agent (script) — sıfır token
- 3 agent (LLM) — gerçekten LLM gerektiren işler:
  - `haftalik-dis-dunya-briefi` (Pzt/Per, proactive-intelligence)
  - `rakip-monitoring` (Pzt 10:05)
  - `dental-lead-gen` (Salı/Cuma)

## No-Agent Dönüşüm Deseni

Basit mesaj/rapor işleri için:

1. Bash script oluştur: `echo` ile çıktı → cron stdout'u Telegram'a iletir
2. `chmod +x` yap
3. Cron'u güncelle: `no_agent=true`, `script=<dosya>`
4. Test: script'i manuel çalıştır

## Script Konumları
```
~/.hermes/scripts/
  ├── kart-denizbank.sh
  ├── kart-yk-hepsiburada.sh
  ├── kart-yk-word-eko.sh
  ├── jeff3-sabah-brifingi.sh
  └── jeff3-aksam-raporu.sh
```
