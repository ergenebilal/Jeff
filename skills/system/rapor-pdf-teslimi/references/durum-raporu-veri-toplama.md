# Durum raporu — canlı veri toplama ve iskelet

Bilal "rapor", "durum raporu", "neredeyiz" dediğinde rapor **ölçülmüş** veriyle yazılır. Her bloğu ayrı tool çağrısı olarak paralel koştur; sonra markdown'ı yaz.

## 1. Sistem sağlığı (tek batch)
```bash
uptime; echo; df -h / | tail -1; echo; free -h | head -2; echo
docker ps --format '{{.Names}}\t{{.Status}}' | head -25; echo
ls -lh --time-style=+%d.%m\ %H:%M /opt/backups/ | tail -5
find /opt/backups/data -maxdepth 1 -mtime -3 -printf '%TY-%Tm-%Td %TH:%TM  %p\n' | sort | tail -6
systemctl is-active hermes-gateway; systemctl --failed --no-legend | head
```
Yazılacaklar: kesintisiz çalışma süresi, disk dolu/boş, bellek, işlemci yükü, ayakta servis sayısı, **en yeni TAM yedeğin tarihi + bütünlük imzası**, mesaj köprüsü durumu. "Yedek var" demek yetmez, tarihini yaz.

## 2. Zamanlanmış görev sağlığı
Arıza teşhisi ve `jobs.json` alan adları için `hermes-operasyon` §12b. Rapora sadece **bulunan arıza + ne yapıldığı** girer (onarıldı/durduruldu); çalışan görevlerin listesi raporda yer kaplamaz.

## 3. Gelir hattı / huni sayıları
```python
import csv, collections
rows = list(csv.DictReader(open('fpc/cevap-log.csv', encoding='utf-8-sig'), delimiter=';'))
print('kayıt:', len(rows), '| kolonlar:', list(rows[0].keys()))   # kolonları gözle doğrula, varsayma
for k in ('nis', 'asama', 'cevap_verdi', 'ilgilendi', 'gorusme_kabul'):
    print(k, dict(collections.Counter((r.get(k) or '').strip().lower() for r in rows)))
```
- İletişim takip tablosu **BOM + noktalı virgül ayraçlı** olabilir: `encoding='utf-8-sig'` + `delimiter=';'`. Yanlış ayraçla okursan tüm satırlar tek kolona düşer ve "veri yok" sanırsın — kolon başlıklarını mutlaka yazdır.
- Hedef havuzu sayıları: taranan işletme / öncelikli havuz / **ölçümle kanıtlanmış** kusurlu işletme (hangi testle doğrulandığı bir cümleyle).

Huni tablosu (sıfır olsa da yazılır):

| Aşama | Sayı |
|---|---|
| Gönderilen mesaj | |
| Gelen yanıt | |
| Kabul edilen görüşme | |
| Kapanan satış | |

Kaydı tutulmamış olabilecek satırı `0` diye kesinleştirme: "son kayıt tarihi X; sonrasında elle gönderim yaptıysan işlenmemiş demektir" diye etiketle.

## 4. Teslim edilen işi doğrula
Rapor "teslim edildi" diyecekse **teslim canlı mı** diye bak (ör. teslim edilen panel/adres yanıt veriyor mu). Kırık bir teslimi "tamam" diye raporlamak güveni bitirir; çalışmıyorsa raporda söyle ve onar.

## 5. Rapor iskeleti (PDF'e çevrilecek markdown)
1. Başlık + tarih/saat + kapsam
2. Tek bakışta (5-6 madde; en kritik bulgu **önce**, iyi haber önce değil)
3. Sistem sağlığı (ölçüm → değer tablosu)
4. Zamanlanmış görevler (bulunan arıza + yapılan)
5. Gelir hattı: kanıtlanmış → hazır olan → huni → "bu tablonun anlamı" (kusur kanıtı var, acı kanıtı yok)
6. Bugün teslim edilenler
7. Bu hafta: **sende olan işler** (süre tahminiyle) / **bende olan işler**
8. Karar bekleyen tek konu (öneri + gerekçe)
9. Tek sayfa eylem sırası

Kapanış notu: "Bu raporun tamamı <tarih> canlı ölçümlerine dayanır; ölçülmeyen sayı yazılmadı, varsayım içeren yerler belirtildi."

Teslim: PDF'e çevir (bu skill'in akışı), doğrula, Telegram'a `MEDIA:` satırı + tablosuz, jargonsuz 4-6 satır özet.
