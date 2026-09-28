# Toplu İş Emri Protokolü

## Tetikleme
Kullanıcı "hepsini sırasıyla hallet", "tümünü yap", "ardışık olarak解决" gibi toplu emir verdiğinde.

## Davranış
1. **Durma, sorma.** Her adımda onay bekleme.
2. **Sıralama:** Kritik → High → Medium → Low önceliğiyle.
3. **İlerleme raporu:** Her 3-5 tamamlanan adımda kısa özet ver ("5/10 tamamlandı, şunlar bitti: X, Y, Z").
4. **Bloke olursa:** Atla, bir sonraki adıma geç, sonda özetle "şu blokeydi, sebep: X".
5. **Bitince:** Tek seferde tüm sonuçları listele — hangisi ✅ hangisi ❌, sebep.

## Hata Yönetimi
- Bir adım başarısızsa → durma, logla, devam et.
- 3+ adım başarısızsa → o bloktaki diğer adımları da atla, sonradan toplu rapor ver.
- Asla "Bu adımda hata oldu, ne yapayım?" diye sorma — kendi kararını ver ve devam et.

## Örnek Akış
```
Kullanıcı: "hepsini sırasıyla hallet"
Jeff: (hiçbir şey sormadan başlar)
  ✅ 1. Port hardening — 0.0.0.0 → 127.0.0.1 (3 port)
  ✅ 2. RAM optimizasyonu — n8n cache temizlendi
  ⏭️ 3. Skill temizliği — atlandı (düşük öncelik)
  📊 Sonuç: 2/3 tamamlandı. 1 atlandı.
```
