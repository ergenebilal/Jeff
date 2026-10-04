# Pablo — yerel taslak sonucunu doğrulama (Jarvis 7.1 / P19)

`local_draft` yalnız `name`, `format` (`txt`, `md`, `json`), `content` ve sistemin
eklediği `request_id` alanlarını kabul eder. En fazla 500.000 UTF-8 bayt.
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
tekrarlanmaz. Kesintiden kurtarma genel kabulü sonraki 7.2 paketidir.

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
