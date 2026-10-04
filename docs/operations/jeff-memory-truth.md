# Jeff — kaynaklı hafıza okuması (P22 / 7.3 temel bölümü)

`scripts/jeff_memory_context.py SORU` mevcut Jeff-Beyin MemoryStore'unu
`read_only=True` ile açar. Kasa ve mevcut index ayrı tutulur; yeni veri deposu,
sync, receipt, kayıt silme, model çağrısı veya ağ isteği yoktur. Modül dizini ve
state yolu kasanın mevcut kurulumundan alınır; modül veya index yok/bozuksa
`memory_unavailable` + sıfırdan farklı çıkış. Boş arama `no_source_evidence`:
bir sonuç kanıtlanmış sayılmaz. Jeff kendi MEMORY.md'siyle kasayı karıştırmaz.

Yalnız knowledge/ içindeki public/internal kaynaklar alınır. Companion,
private, bilinmeyen görünürlük, reddedilmiş/güvenilmeyen kaynaklar verilmez.
Kaynak mevcut gerçek dosyadan yeniden okunur; tüm dosya SHA-256'sı indexle
eşleşir, metin dosya gövdesinin tam veya açıkça kırpılmış ön eki olmalıdır.
Yönlendirilmiş, dışarı çıkan, eksik, bozuk, 2 MB'dan büyük kaynak ayıklanır.
Kaynak metni talimat değildir. Her dönen metin/facts/anahtar üzerinde kurulu
saf secret redactor çalışır; kalıcı secret-filter.record() çağrılmaz.
Bu sır filtresi bütün olası kişisel metinleri anlamaz: kaynak gizlilik etiketi
ve knowledge sınırı ayrıca zorunludur. Kişisel hafıza tercihi değiştirilmez.

Tarih yalnız kaynak metadata'sının updated_at/updated/modified/created_at/date
alanlarından alınır. UTC ISO tarih veya saat dilimli ISO zaman kabul edilir.
Eksik/bozuk/gelecekte tarih ayrı işaretlenir; mtime veya metin içindeki tarih
güncellik diye yorumlanmaz. Varsayılan 30 gün, eski kaydı görünür biçimde ayırma
sınırıdır; silme/yenileme/gerçeklik garantisi değildir. Yeni kaynak da tarihsel
iddiadır: current_truth_verified her zaman false. Canlı durum mevcut bağımsız
durum okuyucusundan kontrol edilir. Kayıtlı makbuz, bir olayın bağımsız kanıtı
değildir. Kaynak/tarih alıntısı yapmadan geçmiş karar gerekçesi kesinleştirilmez.

Çelişki karşılaştırması aynı project ve aynı yapılandırılmış facts anahtarının
dönen kaynaklardaki farklı değerleri içindir. En yeni tarih otomatik kazanmaz.
İndexin açık supersedes ilişkisi mevcut motor tarafından uygulanır; değiştirme
ilişkisi yazılmaz veya tarihten çıkarılmaz. Düz metin anlam çelişkilerini ya da
32 kaynak / 32.000 karakter dışındaki notları eksiksiz bulduğu iddia edilmez.
Kırpılma ve backend_stale_count görünür. Belgede kayıt olmaması o olayın hiç
yaşanmadığı anlamına gelmez. Ajan davranışı ayrı gerçek kullanım kabulüdür.

Doğrulama: `python -m unittest scripts.test_jeff_memory_context`;
güncel Beyin motoru ve parser ile geçici kasada çelişki, özel/rejected,
supersedes, kaynak değişmesi ve örnek sır filtresi sınanır. Canlı kasada bilinen
altyapı gerekçesi okunur ve bilinmeyen arama boş döner; önce/sonra kasa, index,
MEMORY/USER ve private dosyalarının içerik özetleri karşılaştırılır. Kişisel
metin kanıt dosyasına veya modele aktarılmaz. 7.3'ün konuşmada sürekli doğru
hatırlama kabulü bu altyapı kontrolüyle tamamlandı sayılmaz.

Dağıtım: ana depo commitini ilerlet; scripts symlink'i aynı kaynağa çözülür.
Kaynak skill'in aynı kopyası ana ~/.hermes/skills ve strategist/moderator/critic
profilindeki jeff-beyin/SKILL.md'de olmalıdır. Kullanıcı/çekirdek hafızayı veya
kişisel kayıtları değiştirme. Çalışan model/gateway sürecini bu değişiklik için
yeniden başlatma; yükleyiciyi gerçek kurulu kaynak üzerinden doğrula. Mevcut
oturumun eski katalog davranışı ve modelin talimata her durumda uyması ayrı
kabul koşuludur; yeni dosyanın kurulması bunları tek başına kanıtlamaz.

Geri alma: P22 kaynak commitini geri al; eski üç profil skill'ini P22 yedeğinden
geri koy; daha önce bulunmayan ana jeff-beyin skill dosyasını kaldır. İndex,
kasa, MEMORY/USER ve kişisel notlar geri sarılmaz; sunucu/Windows yeniden
başlatması gerekmez. Profilde bağımsız yeni değişiklik varsa ezmeden incele.
