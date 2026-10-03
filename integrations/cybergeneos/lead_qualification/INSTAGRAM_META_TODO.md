# Instagram bağlantısı ve hesap yönetimi

3 Ekim 2026: kullanıcı erişim bilgilerini sağladı ve Instagram hesabının tam
yönetimini Jeff'e yetkilendirdi. Önceki “Meta bağlantısını sonra hallederiz”
ertelemesi kaldırıldı. Bağlı hesap `cybergene.ai`.

## Doğrulanan

- Hesap kimliği ve kendi medya okuması gerçek API çağrılarıyla doğrulandı.
- `instagram_basic`, `instagram_content_publish`, `instagram_manage_comments`,
  `instagram_manage_insights`, `instagram_manage_messages` izinleri granted.
- Dört firmanın güncel resmî sitesinin bağladığı profiller ve toplam on yayıncı
  paylaşımı sunucudan resmî Business Discovery API'siyle okundu.
- Anahtarlar yalnız özel dosyada; araştırma kodu GET kullanıyor. Webhook sırları
  ve uygulama sırrı kopyalanmadı. Kaynaklar model için güvenilmeyen veri.
- Hesap aidiyeti, yayıncı, yayın tarihi ve gözlem tarihi ayrı. Seçimde karşıt
  okuma ve doğrulanmış alıntı şartları sürüyor.

## Sıradaki yönetim işleri — kullanıcı yetkisi verilmiş

1. Kendi hesabı için kalıcı içerik hazırlama/yayınlama akışı, yayımlanan medya
   kimliğiyle sonuç doğrulama ve belirsiz sonuçta tekrar yayımlamadan uzlaştırma.
2. Kendi yayınlarının yorumlarını takip etme ve bağlamla yanıt üretme/yönetme.
3. Bağlı sayfa ve mesaj erişimini gerçek çağrıyla doğrulama; gerekli webhook
   bağlantısı, konuşma uygunluğu ve yinelenen olay denetimiyle DM yönetimi.
4. Hesap/medya istatistikleri ve nitelikli talep → görüşme sonuçlarıyla ölçüm.

Yetki, modülün tamamlandığı veya bir gönderinin iletildiği kanıtı değildir.
Bu bağlantı testi paylaşım, yorum veya mesaj yayımlamadı. Başka firmaların DM
trafiği veya iç sistemleri kamusal açıklamalardan çıkarılamaz. İzin vermek
Instagram'ın bütün özelliklerinin API tarafından sunulduğu anlamına gelmez.
