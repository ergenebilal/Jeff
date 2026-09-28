# Memory Yönetimi

## Limit

- Varsayılan: 2,200 chars (`config.yaml` → `memory.memory_char_limit`)
- 15.06: 8,000'e çekildi
- **16.06 (sonsuz hafıza):** `hermes config set memory.memory_char_limit 50000` ile 50K'ya çekildi
  - `hermes config set memory.user_char_limit 5000` (user profil limiti de 1,375 → 5K)
  - `hermes config set` CLI kullanılır, config.yaml'a direkt yazılamaz (güvenlik engeli)

## Memory Consolidation Workflow

Memory %80+ dolduğunda veya "sonsuz hafıza" istendiğinde uygulanır:

### Adımlar

1. **Tüm memory entry'lerini oku** (memory tool dönen listeyi kullan)
2. **Kategorize et:**
   - KALICI: sistem kuralları, kullanıcı politikaları, kritik refleksler, stratejik iş yönü
   - SIK KULLANILAN: ortam notları, portlar, servis bilgileri — skill'e taşınabilir
   - STALE: tamamlanmış fazlar, tarih olmuş durum raporları, geçici task notları — sil
3. **Consolidate:** Benzer konudaki 3-7 küçük entry'yi tek entry'de birleştir
   - Örn: "SİSTEM KURALLARI" tek entry — halüsinasyon refleksi + çarpan etkisi + 90/10 otonomi + özeleştiri #9 + kullanıcı beklentisi + kalite + iletişim stilleri
   - Örn: Lead yönetimi — kanban + URL + demo formatı + workflow hepsi tek entry
4. **Sil:** Önce `memory(action='remove', old_text='...')` ile eski entry'leri temizle
5. **Ekle:** Sonra `memory(action='add', content='...')` ile consolidated entry'yi ekle

### Hedef
- Entry sayısı 25+ → 12-15
- Kullanım %89 → %40-55
- Her entry anlamlı ve gerekli

### Memory'de kalması gerekenler:
- Kullanıcı politikaları (iletişim kuralları, karar prensipleri)
- Kritik refleksler (halüsinasyon, çarpan etkisi)
- Sistem mesaj politikası
- Stratejik iş yönü
- Sistem sabitleri (portlar, servis yolları, fix'ler)

### Skill'e taşınması gerekenler:
- IP adresleri, port numaraları, token'lar
- Backup prosedürleri
- Tool/servis yapılandırma detayları
- Domain/DNS bilgileri
- API anahtar referansları (.env'de tutulur, memory'de sadece "key .env'de" notu)

## Session DB (Yedek Bellek)

Memory'de olmayan ama geçmiş session'larda geçen bilgiler için:
- `session_search(query)` ile FTS5 araması
- Skill'lerdeki referans dosyaları
- `hermes-ortam-notlari` skill'i (geniş ortam dökümü)

## Sistem Mesaj Politikasi (14.06.2026)

**Kural:** Tüm cron/system mesajlarının muhatabı Jeff'tir. Bilal'e sadece çözüm gerektiren PROBLEM bildirilir. Rutin başarılı çalışmalar asla Bilal'e gitmez, local'e loglanır.

**Uygulama:**
- Tum cron job'lar `deliver: local` olmali
- Sadece dogrudan Bilal'e gitmesi gereken job'lar (ornegin baska bir numaraya giden denetim hatirlatici) deliver override eder
- Cron job'lari guncellerken `cronjob(action='update', job_id='xxx', deliver='local')`
