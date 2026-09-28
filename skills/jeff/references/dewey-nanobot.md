# Dewey = Nanobot — Delegasyon Protokolü (hafızadan taşındı 15.09.2026)

- Bilal, **Nanobot**'a "Dewey" diyor. Eski adı Jeff Nano (21.08.2026'da değişti).
- Ağ geçidi: `127.0.0.1:18791` (`~/.nanobot/config.json`), servis: `python3.11 -m nanobot gateway --foreground --port 18791`.
- 8 servis watchdog'ı olarak kuruldu, sonra subagent sistemine dönüştü; `max_concurrent_subagents=5`.
- **İş bölümü:** Basit/tekrarlayan işler (basit cron, hatırlatma, takip, toplu tarama) → Dewey. Strateji/karar/onay/hafıza yazımı → Hermes/Jeff.
- Çağırma: `~/.hermes/scripts/nanobot_task.sh 'PROMPT' 'session-id'` veya `timeout 60 nanobot agent --message '...' --session 'spawn-N'`.
- Deterministik paralel iş için `swarm` değil **`spawn`** kullanılır (label + task, izole).
- Kalite kuralı: Nanobot çıktısı doğrudan Bilal'e gitmez — önce QA/doğrulama.
