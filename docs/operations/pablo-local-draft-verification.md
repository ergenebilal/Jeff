# Pablo — yerel taslak sonucunu doğrulama (Jarvis 7.1 / P19)

`local_draft` yalnız `name`, `format` (`txt`, `md`, `json`), `content` ve sistemin
eklediği `request_id` alanlarını kabul eder. P20 ile isteğe bağlı `deadline_at`
(UTC Unix saniyesi, son tarih) eklenmiştir; bu bir çalıştırma takvimi değildir.
En fazla 500.000 UTF-8 bayt.
İstenen dosya ve içerik görev kaydına bağlıdır; keyfi yol veya komut alınmaz.
Dosyalar Windows node klasörünün `verified-drafts/<request-id SHA256>/` alanında.
Var olan farklı dosya ezilmez; dışarıya mesaj gönderilmez.

İşi yapan kodun başarılı cevabı doğrulama kanıtı değildir. Guard beklenen içeriği
önceden sabitler; yazma işleminden sonra dosyayı ayrı olarak açıp okur, boyutunu ve
SHA256 özetini karşılaştırır. Symlink/reparse, dizin, fazla büyük dosya, okuma
hatası veya okuma sırasında değişen dosya başarılı sayılmaz. Bu dosya doğrulaması,
işletim sistemi izolasyonu ya da genel GUI doğrulayıcısı değildir.

Sonuçlar: `SUCCESS` + `outcome_verified=true`; farklı dosyada
`OUTCOME_MISMATCH`; okunamayan/yok dosyada `VERIFICATION_UNAVAILABLE`.
Kanıtta içerik bulunmaz; beklenti/ölçüm özetleri, boyut, istek bağı ve ölçüm zamanı
vardır. Aynı istek yeniden gönderilince kayıtlı sonuç döner; yeni ölçüm değildir.
İçerik değişirse aynı istek kimliğiyle çalıştırılamaz. Belirsiz sonuç otomatik
tekrarlanmaz. P20 kesintiden sonra yalnız dosya gözlemine dayalı toparlanmayı
ekler; genel GUI, müşteri teslimi ve günlerce süren çok adımlı iş yürütme açık kalır.

Sunucuda küçük bir yerel taslak için:

```sh
/home/hermes/.venv/bin/python /home/hermes/scripts/pablo_local_draft.py --file /path/to/local-draft.txt --name note --format txt
```

Bu yardımcı gerçek Bridge → Pablo yolunu kullanır; komut çalıştırma veya müşteri
gönderimi yapmaz. Görev sonucu Windows dosya gözlemiyle eşleşirse bunu gösterir.
Bridge'in eski görev tablosundaki `unverified` etiketi korunur; bu kayıt sunucuda
ayrıca bağımsız doğrulanmış gibi sunulmaz. Uçtan uca canary kanıtı ayrıca Windows
dosyasını yerel okuyucu ile karşılaştırır.

Kontrol: `PYTHONPATH=pablo:. python -m unittest pablo.test_local_draft_verification scripts.test_pablo_local_draft`.

## Kalıcı iş takibi (P20 / Jarvis 7.2 dar kapsam)

Mevcut `task-journal.sqlite3` tek Pablo iş defteri olarak korunur; yeni ikinci
veritabanı yok. Aşama, durum, sonraki adım, beklenen kişi/kanıt, varsa son tarih,
son güncelleme ve içerik taşımayan aşama geçmişi aynı görev kimliğine bağlıdır.
Son tarih verilmemişse bilinmiyor olarak gösterilir; eski tarihler uydurulmaz.
Tamamlanan, reddedilen ve eski onay arşivine alınan işler açık listeye girmez.
Hatalı/belirsiz sonuçlar açık kalır; liste sayfalıdır, toplam sayı gösterilir.

Jeff sunucusunda:

```sh
/home/hermes/.venv/bin/python /home/hermes/scripts/pablo_work_status.py
/home/hermes/.venv/bin/python /home/hermes/scripts/pablo_work_status.py --task-id TASK_ID
/home/hermes/.venv/bin/python /home/hermes/scripts/pablo_work_status.py --task-id TASK_ID --reconcile
```

İlk ikisi yalnız okur. Üçüncüsü yalnız yerel taslağın kayıtta sabitlenmiş dosyasını
okur; eylem/yazıcı/komut çalıştırmaz. GET `/work`, GET `/work/<id>` ve POST
`/work/<id>/reconcile` mevcut IP ve gizli erişim anahtarı korumasını kullanır.
Görev içeriği/komutu veya anahtar bu görünümde yoktur. Eski `/tasks/<id>` kayıtlı
sonucu verir; taze gözlem iddiası taşımaz. Bridge’in `unverified` etiketi korunur.

Pablo işçi döngüsü açıldığında ve sonra en erken 60 saniyede bir yarım kalmış
yerel taslakları yalnız gözlemle kontrol eder. Bridge’in eski teslimi yeniden
sorgulaması da aynı yolu kullanır. Dosya zaten beklentiyle eşleşiyorsa kapatılır;
yeniden yazılmaz. Dosya yok/yanlış/okunamıyorsa ve ilk işlem için 300 saniyelik
gözlem bekleme süresi dolmamışsa iş IN_PROGRESS kalır. Süre dolunca doğrulama
eksikliği açık gösterilir; otomatik yeniden yürütme yapılmaz. Aynı görevle gelen
tekrar kayıtlı sonucu döndürür. Oluşmuş dosya değişmeden kaldıysa kapanış yalnız
sonuç kanıtıdır; eski yazma eyleminin kanıtlandığı iddia edilmez.

Eski genel komutların beklenen sonuç sözleşmesi yoktur: açık `legacy_unknown`
olarak görünür, tarihler bilinmiyorsa boş kalır ve asla tekrar çalıştırılmaz.
Yeni bir görev oluşturarak kör tekrar yapmak toparlanma yöntemi değildir.
Takip görünümü yeni rutin bildirim göndermez. Bu paket çok adımlı/günlere yayılan
iş planlayıcısı, tüm sistemlerin tek arayüzü veya yeni sunucuya tam dönüş provası
değildir; 6.3 ve 7.4–7.6’nın geniş kabulü ayrıca açık.

Kontrol: `PYTHONPATH=pablo:. python -m unittest pablo.test_work_tracking scripts.test_pablo_work_status`.

P20 geri alma: sunucuda P20 commitini geri al; Windows'ta P20 kaynak/deployment
yedeğini geri koy ve yalnız boş Pablo'yu yeniden başlat. Ek SQLite sütunları ve
`work_events` eski kodun çalışmasına engel değildir; veritabanını eski yedekle
geri sarmayın. Dosyalar, güncel iş/onay kayıtları ve aşama geçmişi korunur.

Dağıtım: test edilen kaynak commitini sunucu ana deposuna hızlı ileri al;
Windows'ta `hermes_node.py`, `pablo_task_guard.py`, `pablo_local_drafts.py` ve
`deployment.json` güncellenir. Yürüyen güncel iş yokken yalnız Pablo yeniden
başlatılır; `/ping` sekiz yüklenen kaynak özetini göstermeli. Diğer kurulu Windows
dosyaları kendi önceki kaynağıyla eşleşmelidir. Gizli ayarlar değiştirilmez.

Geri alma: P19 commitini ana depoda `git revert` ile geri al; Windows kaynaklarını
ve önceki `deployment.json` dosyasını paket yedeğinden geri koy; güncel işler
boşken yalnız Pablo'yu yeniden başlat. Eklenen modül geriye alınan node tarafından
kullanılmaz; arşiv olarak kalabilir. Onay/görev veritabanları veya taslak dosyaları
geri sarılmaz, silinmez. Paket manifesti kaynak özetlerini ve yedekleri kaydeder.
