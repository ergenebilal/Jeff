# Pablo — kalıcı çok adımlı iç iş planı (P21 / Jarvis 7.2)

İlk kabul yalnız özel yerel taslak dosyaları içindir. En fazla 20 sıralı adım;
her dosya en fazla 500.000, bütün içerik en fazla 2.000.000 UTF-8 bayt.
Kabuk/GUI/mesaj/ödeme/sosyal yayın eylemi bu şemada yok. Pazarlama kuralları ve
ajan araç izin listesi değiştirilmez. Modelin kendi başına doğru plan yapacağı
iddiası değildir; önceden tanımlanan iç iş planını güvenle izleme altyapısıdır.

Mevcut `task-journal.sqlite3` kullanılır. Ana planın girdisi değişmez özetle
bağlıdır; çocuk kimlikleri ana kimlik ve adım adından deterministik türetilir.
Çocuk bağı ilk icra talebiyle aynı işlemde kaydedilir. İkinci bir defter/plan
veritabanı yoktur. Sonraki adıma geçmeden önce önceki dosyaların gerçek içeriği
yeniden okunur. Yanlış, yok veya okunamayan eski sonuç sonraki adımı durdurur.

Örnek `plan.json` (tarihler UTC Unix saniyesidir):

```json
{
  "goal": "İki özel taslağı sırayla hazırla",
  "deadline_at": 1791400000,
  "steps": [
    {"name": "first", "draft": {"format": "txt", "content": "İlk taslak"}},
    {"name": "second", "draft": {"format": "md", "content": "İkinci taslak"},
     "not_before": 1791300000,
     "wait_for": {"kind": "event", "key": "input_ready"}}
  ]
}
```

Tarihlerin örnek olduğunu unutmayın; gerçek işte uygun tarih belirlenir. Her
adım önceki bütün adımlar doğrulanınca çalışabilir. `not_before` geçmeden veya
bekleme bildirimi gelmeden yeni adım talebi oluşturulmaz. Son tarih aşılmışsa
yeni adım başlamaz, iş açık kalır. İşçi döngüsü Pablo açıldığında ve en erken
60 saniyede bir devamı değerlendirir. Bu hassas zamanlı bir takvim hizmeti veya
bilgisayar kapalıyken iş yürütme garantisi değildir.

Jeff sunucusunda:

```sh
/home/hermes/.venv/bin/python /home/hermes/scripts/pablo_work_plan.py --task-id MY_PLAN --file /path/to/plan.json
/home/hermes/.venv/bin/python /home/hermes/scripts/pablo_work_status.py --task-id MY_PLAN
/home/hermes/.venv/bin/python /home/hermes/scripts/pablo_work_plan.py --task-id MY_PLAN --signal second --key input_ready --source "İlgili girdi hazır olduğuna dair kayıt"
/home/hermes/.venv/bin/python /home/hermes/scripts/pablo_work_plan.py --task-id MY_PLAN --advance
/home/hermes/.venv/bin/python /home/hermes/scripts/pablo_work_plan.py --task-id MY_PLAN --cancel
```

Olay bildirimi kaynağıyla kaydedilen **beyandır**; dış dünyada sonucu veya başka
bir kişinin yanıtını bağımsız doğrulamaz. Doğrulanmış dosya sonucu ayrı ölçülür.
`kind: person` için `who` etiketi zorunludur. Bu beklemenin bildirimi ajan
anahtarıyla kaydedilemez: HTTP çağrısı ayrıca mevcut, ajan anahtarından farklı
`X-Approval-Key` sahip anahtarını ister. Ajan CLI bu anahtarı okumaz ve kişi
yanıtını kendiliğinden üretmez. Bu kayıt finansal/harici eylem onayı değildir;
canonical onay defterine olay eklenmez. Sohbet/panelde bir kişi yanıtı arayüzü
eklemek 7.6'nın ayrı kapsamıdır; bu altyapı çağrısını tamamlanmış arayüz saymayın.

HTTP: `POST /execute` eylemi `local_draft_plan`; durum `GET /work/<id>`;
devam `POST /work/<id>/advance`; bildirim `POST /work/<id>/signal` gövdesi
`step`, `key`, `source`; durdurma `POST /work/<id>/cancel`. Mevcut IP ve erişim
anahtarı korunur. `POST /work/<id>/reconcile` yalnız mevcut dosyaları gözlemler,
yeni adım oluşturmaz. Ana planın `/execute` tekrarı kayıtlı yanıtı döndürür;
değiştirilen plan aynı kimlikle çalışamaz. Devam, olay ve durdurma ayrı açıktır.

Kayıt `SUCCESS` ancak bütün dosyalar bağımsız gözlemle eşleşince oluşur.
Çocukta icra talebi varsa yeniden yürütülmez: var olan dosya gözlemlenir;
belirsizlik varsa iş açık kalır. Hiç talep edilmemiş sıradaki adım farklı,
sabit kimliğiyle ilk kez çalışabilir. Kesintiden sonra tamamlanmış adımın
dosyası tekrar yazılmaz. Aşama/bildirim/arşiv kayıtları eklemeli geçmiştedir.
İptal kabul edildikten sonra yeni adım talebi oluşturulmaz; önceden talep edilmiş
adımın dosyası silinmez/geri alınmaz. İptal, işin sonucu doğrulandı demek değildir.
Sonradan yinelenen başarılı sonuç tarihli kayıttır, taze ölçüm değildir.

Çocuklar genel açık listede ikinci görev gibi sayılmaz; ana planda görünür.
Eski, oluşturma tarihi bilinmeyen ERROR/BLOCKED/FAILED kayıtları, onay/claim veya
bekleyen teslim taşımıyorsa sessiz geçmişe alınır. Kaynak kayıt/status/parametreler
değişmez; sonuç **doğrulanmamış** kalır. Yaşları uydurulmaz. UNKNOWN,
IN_PROGRESS, PENDING_VERIFICATION ve eski APPROVED durumları arşivlenmez.
Varsayılan liste hem görünür açık sayıyı hem geçmişteki doğrulanmamış sayıyı
gösterir. Geçmişi görmek için `pablo_work_status.py --include-history`; tek görev
kimliğiyle eski kaydı okumak hâlâ mümkündür. Bildirim veya yeniden yürütme yok.

Kabul: `PYTHONPATH=pablo:. python -m unittest pablo.test_work_plans scripts.test_pablo_work_plan`.
Gerçek süreç çıkışıyla adım sonrası, dosya yayımı sonrası ve ana sonuç kaydı
öncesi kesintiler sınanır. İki günlük bekleme saati testte açıkça ilerletilir;
bu iki gün gerçek kullanım yapılmış demek değildir. Canlı prova ayrıca gerçek
Windows süreci/yazıcı kesintisi ve yeniden açılışla yapılır. Yedi günlük kullanıcı
yükü ölçümü 7.5'tir, bu paket onu tamamlamaz.

Dağıtım: test edilen kaynak commitini sunucuda hızlı ileri al; boş Pablo'da
node, guard ve yeni plan modülünü kur. `/ping` dokuz süreç kaynak izini göstermeli;
kurulu pazarlama gateway dahil on dosya kaynakla eşleşmelidir. Ayar/işletme kodu
değişmez. Geri alma: P21 commitini geri al; Windows'ta P21 node/guard/deployment
yedeğini geri koy, boş Pablo'yu yeniden başlat. Yeni modül kullanılmadan kalabilir.
SQLite ekleri eski kodla uyumludur; görev/onay veritabanlarını veya dosyaları
geri sarmayın/silmeyin. Bekleyen P21 planlar eski kodda çalışmaz; geçişteki
durdurma sınırı ve kaydı korunur, sessizce tamamlandı sayılmaz.
