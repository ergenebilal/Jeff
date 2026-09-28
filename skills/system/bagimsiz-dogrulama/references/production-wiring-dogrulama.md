# Production Gerçeği — Wiring Doğrulama Tarifi

Amaç: "X tamamlandı / entegre edildi" iddiasını **production'ın kendisinden** doğrulamak.
Kod okumak yetmez; kanıt process'ten, log'dan, kayıttan ve kayıt ID'sinden gelir.

## 1. Çalışan process ve import yolları

```bash
pgrep -af "hermes_cli.main gateway"
for p in $(pgrep -f "hermes_cli.main gateway"); do
  echo "PID=$p"; tr '\0' ' ' < /proc/$p/cmdline; echo
  readlink /proc/$p/cwd; readlink /proc/$p/exe
  ps -o lstart=,etime= -p $p
  ls -l /proc/$p/fd 2>/dev/null | grep '\.py$'
done
```

Production ortamında gerçek modül yolu:
```bash
python3 -c "import agent.conversation_loop as m; print(m.__file__)"
```

Dev checkout ile canlı `site-packages/` AYRI dosyalardır — hangisinin yüklü olduğunu mtime ile kaydet:
```bash
stat -c '%y | %s bytes | %n' <dosya1> <dosya2>
```
NOT: `run_agent` gibi modüller `site-packages/agent/` altında değil, `site-packages/` **kökünde** olabilir. Aramayı kökte de yap.

## 2. SET vs READ — özellik inert mi?

```bash
grep -rn "<sembol>" <canli-kok>/ <paket>/ | grep -v '\.pyc'
```
- Yalnız **atama** satırı çıkıyor → özellik tüketilmiyor, davranış değişmiyor. "Wired" deme.
- **Okuma** satırı (guard, `getattr`, `.get`, `if ...: return`) çıkıyor → gerçekten tüketiliyor.

## 3. Zincir halkaları

```bash
grep -rn "from <modul> import\|import <modul>" <canli-kok>
grep -n "<fonksiyon_adi>" <dosya>
```
Her halka için: STATUS + FILE:satır + FUNCTION + çağrı yeri. "Entegre" gibi kanıtsız sıfat kullanma.

## 4. ID ile uçtan uca eşleştirme

Karar/audit kaydını zincirin iki ucunda aynı ID ile ara:
```bash
grep -n "<decision_id>" <log1> <log2>
ls <kayit_dizini>/ | grep "<decision_id>"
```
ID iki uçta da varsa zincir gerçek; yoksa kopuk halka. Bu, "BLOCK gerçekten action'ı engelledi mi?" sorusunun en ucuz kanıtıdır.

## 5. Kayıtları deploy zamanına göre segmentle

Kodun mtime'ı ile kayıt zamanlarını karşılaştır. Kod 15:09'da kurulduysa 12:15 kayıtları o kodu test etmiyordu.
Bir "oran" düşük görünüyorsa (örn. 10 olaydan 1'i işlenmiş) önce segmentle — genelde cevap "koddan önceki kayıtlar" olur.

## 6. Baseline metrikleri programatik çıkar

```python
import json
from collections import Counter
rows = [json.loads(l) for l in open(LOG) if l.strip()]
dec  = [r for r in rows if "action" in r and r.get("event") != "action_enforcement"]
Counter(d.get("action") for d in dec)
lats = sorted(d.get("latency_ms", 0) for d in dec if d.get("action") == "blocked")
print(len(lats), min(lats), max(lats), sum(lats)/len(lats))
```
Kovalara ayır; her kova için **n + min/max/ortalama + kaynak dağılımı + oran** ver. Göz kararıyla sayma.

## 7. Mod bayrağını oku (dry_run / stub / mock)

```bash
grep -n "dry_run\|stub\|mock\|_env_mode" <modul>.py
```
Stub/dry modda çıktı deterministiktir (hep aynı verdict, boş gövde, sabit confidence) → çıktı **kalitesi** ölçülemez.
Bunu raporda açıkça belirt; "karar kalitesi iyi/kötü" deme.

## 8. Backup diff ile implementasyon doğrulama

```bash
diff <(cat X.bak-adimN) <(cat X)
```
Ameliyatın tam olarak ne eklediğini gösterir. "Mevcut implementasyon gerçekten var mı?" sorusunu diff'ten cevapla.

## 9. Sınırlar (audit disiplini)

- Riskli/yıkıcı yolu kapatmak için production'da riskli test **yapma** → `UNVERIFIED` bırak, gerekçesini yaz.
- Testleri izole çalıştır: `HERMES_HOME=$(mktemp -d) python3 -m pytest tests/ -q`; sonucu **TEST ONLY** etiketle, E2E kanıtı sayma.
- Audit sırasında **hiçbir değişiklik** yapma (kod/config/deploy/restart/migration/refactor).
- Çıktı: tek MD dosya + Telegram'a `MEDIA:` ile; verdict tek satır, kanıt ≤10 madde.
- Aşırı uzun inline shell payload'ları hardline guard'a takılır — komutu parçala; guard kaydettiği script yolunu önerir (`bash <cache>/blocked-scripts/blocked-*.sh`).

## 10. Setter sınıflandırması — test-only atama tuzağı

Bir ayar/bayrak production'da okunuyorsa **kimin set ettiğini** bul ve atamanın hangi dosyada
olduğunu sınıflandır:

```bash
grep -rnE "<sembol>\s*=" <paket>/ <repo>/ | grep -v '\.pyc'   # sadece ATAMALAR
```

- Atama yalnız `tests/` altında → özellik production'da **ÖLÜ**. Test, production'ın asla
  ulaşmadığı bir seam'e değer enjekte ediyor; yeşil test davranış kanıtı değildir.
- Tipik kalıp: `cfg = AutonomyConfig.from_mapping(getattr(agent, "_x_section", None))` ve
  `_x_section`'ı set eden tek satır `tests/...` içinde → production'da `None` → varsayılan
  (`0`/`False`) → `if cfg.<esik> > 0:` bloğu hiç açılmaz; config dosyasındaki blok INERT kalır.

Resolver'ı iki girdiyle doğrudan çağır, farkı göster:
```bash
python3 -c "
from agent.autonomy import AutonomyConfig as C
print('dict ->', C.from_mapping({'success_judge_every': 10}).success_judge_every)
print('None ->', C.from_mapping(None).success_judge_every)"
```
`dict → 10`, `None → 0` ise ve production yolunda `None` geçiyorsa raporun "config çözümü PASS"
satırı bir **seam testidir** — gerçek kullanımdaki değeri değil, testin enjekte ettiği değeri ölçmüştür.
Rapora "test ortamında doğrulandı, gerçek kullanımda DEĞİL" yaz.

## 11. Durağan canlı veri — beklenen sonuç mu, kanıt mı?

Deploy sonrası tablo/log değişmediğinde iki yönlü sor:

1. **O veriyi üretecek olay gerçekleşti mi?** Deploy'dan bu yana tamamlanmış tur/olay sayısı 0 ise
   (ör. süreç başlangıcı `ps -o lstart=` / `ActiveEnterTimestamp` sonrasında yeni kayıt yok)
   değişmemesi **beklenen** sonuçtur — ne doğrulama ne çürütme. Bunu "hâlâ bozuk" diye okuma.
2. **"İlk turlarda dolacak" bir HİPOTEZDİR**, doğrulama değil. Rapora `GÖZLEM SÜRÜYOR` yaz;
   gerçekleşmiş gibi anlatma. Kanıt, olay gerçekleştikten sonra aynı tabloda görülen ilk yeni satırdır.

Tersi de geçerli: boş tablo (0 failure / 0 lesson / 0 attempt) tek başına "halka ölü" demek değildir —
halkayı hangi olayın beslediğini ve o olayın gerçekleşip gerçekleşmediğini ayrıca göster.
