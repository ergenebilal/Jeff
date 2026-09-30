# Jeff & Pablo — CyberGene'in dijital çalışanı

Jeff (sunucuda çalışan beyin) ve Pablo (Windows PC'de çalışan eller), CyberGene'in pazarlama ve operasyon süreçlerini yürüten tek bir dijital çalışan olarak tasarlanmıştır. Bu repo onun kaynak kodudur.

---

## Klasörler

- `jeff2/bridge/` — Jeff ↔ Pablo görev/onay köprüsü (FastAPI, port 7700), dayanıklı task ledger, güvenlik testleri. Şu an üretimde çalışan çekirdek.
- `pablo/` — Windows yürütme düğümü: `hermes_node.py`, onay kilidi (`pablo_task_guard.py`), pazarlama otomasyon hattı (lead havuzu, Telegram onay kartları, playbook'lar, Instagram editoryal kapısı).
- `scripts/` — operasyonel betikler (sabah brifingi, lead radarı, CI kapıları). Hangilerinin aktif olduğu `ACTIVE_CODE.json`'da.
- `skills/` — sahada işe yaramış prosedür kütüphanesi (system, product, self, orchestration, research, social-media ve diğerleri).
- `jeff2/_on_hold/` — Ağustos 2026'da arşivlenen eski mimari ve çalışmış ama dondurulmuş sistemler; ayrıntı için `jeff2/README.md`.
- `backup-jeff/` — Jeff'in kendi yedek/geri yükleme betikleri.
- `SOUL.md` — 99/1 otonomi ilkesi ve çalışma anayasası.

Aktif kod haritası (hangi dosya production, hangisi arşiv): `ACTIVE_CODE.json` ve `ACTIVE_CODE.md`.

---

## Bilinmesi gerekenler

- Pablo'nun canlı kopyası `C:\CyberGene\HermesNode` git deposu değildir. Buradaki kod (2026-09-29 itibarıyla) repoyla senkrondur; Pablo'da yapılan her değişiklik repoya da yansıtılmalıdır. Bilerek repo dışında bırakılanlar: `config.json` ve `.env` (gizli bilgiler), yedek/çalışma kopyaları (`*.bak*`, `*_workcopy.py`, `patch_*.py`) ve `pablo_human_behavior.py`.
- `pablo_human_behavior.py` (sosyal platformlarda bot tespitinden kaçınmaya yönelik "insansı davranış" katmanı) herkese açık repoda tutulmaz: platform şartlarına aykırıdır ve hesap kapanma riski taşır. Kod bu modül olmadan da çalışır (içe aktarma isteğe bağlıdır).
- Bu repo herkese açıktır. Kimlik bilgisi, token ve anahtar hiçbir zaman commit edilmez; ortam dosyaları ve `config.json` repo dışında tutulur.
