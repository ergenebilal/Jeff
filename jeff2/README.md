# jeff2/ — Bridge, arşiv ve tasarım geçmişi

`jeff2/` altında bugün fiilen çalışan tek şey `bridge/`'dir. Geri kalanı tarihsel arşiv veya hiç uygulanmamış spec'lerdir — aşağıda hangisinin ne olduğu açıkça ayrılıyor. Bu dosya daha önce (28 Ağustos 2026'dan önce yazılmış, hiç güncellenmemiş bir sürümde) burada artık var olmayan bir "5 departman / 4 gelir motoru" mimarisini anlatıyordu; o mimari 20-21 Ağustos 2026'da resmen arşivlendi (bkz. aşağıda) ve yerine gelmedi — CyberGene bugün jeff2/bridge'in Jeff↔Pablo görev/onay hattı üzerinden çalışıyor.

---

## Aktif: `bridge/`

Jeff (Linux sunucu, Aider) ↔ Pablo/Alfred (Windows, Guardian onay kilidi) arasındaki gerçek üretim köprüsü. `jeff_bridge_api.py` (FastAPI, port 7700), `task_contract.py` (dayanıklı task ledger + bağımsız verifier), `aider_runner.py`, `alfred_client.py`, kapsamlı güvenlik testleri. `ACTIVE_CODE.json` (repo kökü) bu katmanın hangi dosyalarının production entrypoint olduğunu makine-okunabilir olarak listeler; oradaki liste bu dosyadan daha güncel kabul edilmelidir.

Köken: `specs/aider-alfred-bridge-spec.md` (v1.0) — bu spec fiilen uygulanmış, tek istisna. Diğer spec (`specs/jeff-4.0-multi-agent-upgrade.md`, 10.08.2026) hiç kod haline gelmeden terk edildi.

## Arşiv: `_on_hold/` (20-21 Ağustos 2026'da donduruldu)

Jeff 3.0'ın "CEO/Executive Layer + 5 Departman + 4 Gelir Motoru + Governance" mimarisinin kalıntısı. Tek tip bir iskelet değil — üç farklı olgunluk seviyesi var:

- **Hiç koda dönüşmemiş plan/charter belgeleri:** `departments-20260821/`, `engines-20260821/`, `executive-20260821/`, `governance-20260821/`, `workers-20260821/`, ayrıca `marketplace/`, `multi_tenant/`, `prediction_engine/`, `simulation_engine/` (bunlar Faz 4/5 spec'leri, hiç başlanmadı).
- **Gerçekten bir süre production'da çalışmış, sonra bilinçli olarak durdurulmuş sistemler:** `hq-20260821/app.py` (1876 satır, gerçek lead verisiyle çalışan bir Flask görev paneli), `decision_engine-20260821/decision_pipeline.py` (26 gerçek kayıtla çalıştı), `revenue-20260821/` (gerçek dijital ürünler üretildi; `venture_registry.json` dürüst "kill" kararlarını kayıt altına alıyor).
- **Gerçek bir altyapı denetimi:** `reports-20260821/optimization/` (docker/ufw/port taraması bulgularıyla).

Bu klasördeki hiçbir dosya aktif `bridge/` koduna import edilmiyor veya referans vermiyor. `ACTIVE_CODE.md` bunu "production import path değil" diye zaten doğru işaretliyor.

Kökenini anlamak için: `roadmap/VAKA_ANALIZI.md` (Jeff 3.0 mevcut durum/dönüşüm planı — `_on_hold`'daki her klasör bu dokümandaki bir faza karşılık gelir).

## `self_healing_sandbox/`

`bridge/self_healing_engine.py`'nin test fixture'ları (kasıtlı bozuk kod örnekleri dahil). Production import path değil.

## `specs/`

- `aider-alfred-bridge-spec.md` — uygulandı, bkz. `bridge/` yukarıda.
- `jeff-4.0-multi-agent-upgrade.md` — asla uygulanmadı, terk edildi.

---

## Hızlı Başlangıç

```bash
ls jeff2/bridge/          # Aktif Jeff↔Pablo köprüsü
cat ACTIVE_CODE.json      # Gerçek production dosya haritası (repo kökü)
python scripts/run_active_tests.py --group bridge
```
