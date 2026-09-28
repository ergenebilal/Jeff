# Risk Register
# Generated: 2026-08-17T14:15:00+03:00

risks:
  - id: RISK-001
    title: Sunucu dışı yedek doğrulanmamış
    severity: CRITICAL
    category: Backup & DR
    description: |
      jeff-backup.tar.gz (187 MB) mevcut ancak kapsamı, güncelliği
      ve restore başarısı doğrulanmamış. Dış yedek (Drive/Backblaze)
      durumu bilinmiyor.
    impact: Sunucu felaketinde tüm veri kaybı
    probability: ORTA
    mitigation: |
      1. jeff-backup.tar.gz kapsam listesi çıkar
      2. Dış yedek durumunu doğrula
      3. İzole ortamda restore testi yap
      4. Otomatik dış yedek kur
    status: OPEN
    owner: jeff

  - id: RISK-002
    title: hmpanel-panel Docker socket mount
    severity: CRITICAL
    category: Security
    description: |
      /var/run/docker.sock hmpanel-panel container'ına mount edilmiş.
      Bu, container'dan docker komutları çalıştırılarak yeni privileged
      container açılmasına olanak tanır.
    impact: Container escape ile tam host kontrolü
    probability: DÜŞÜK (erişim kısıtlı olmalı)
    mitigation: |
      1. Docker socket'i kaldır veya read-only mount et
      2. HM Panel'in socket'e gerçekten ihtiyacı olup olmadığını doğrula
      3. Alternatif: Docker API proxy kullanımı
    status: OPEN
    owner: jeff

  - id: RISK-003
    title: RAM kullanımı %81
    severity: HIGH
    category: Resources
    description: |
      31 GB RAM'in 24.8 GB'ı kullanımda. Docker konteynerleri
      yalnızca 1.03 GB (~3.3%) kullanıyor. Kalan ~24 GB'ın
      hangi süreçler tarafından tüketildiği bilinmiyor.
    impact: OOM riski, servis kesintisi
    probability: ORTA
    mitigation: |
      1. ps_mem ile host-seviyesi RAM dağılımı ölç
      2. En çok RAM tüketen 10 süreci belirle
      3. Gereksiz servisleri tespit et
      4. RAM limitleri tanımla
    status: OPEN
    owner: jeff

  - id: RISK-004
    title: hmpanel-host-agent privileged=true
    severity: HIGH
    category: Security
    description: |
      Container privileged mode'da ve pid=host ile çalışıyor.
      Tüm host dosya sistemine erişim var.
    impact: Container escape ile tam host erişimi
    probability: DÜŞÜK
    mitigation: |
      1. Privileged flag'ini kaldır
      2. Gerekli capabilities'i sadece ekle (CAP_SYS_ADMIN vb.)
      3. Root bind'i (/ -> /host) kaldır
    status: OPEN
    owner: jeff

  - id: RISK-005
    title: 7 container :latest tag kullanıyor
    severity: HIGH
    category: Deployment
    description: |
      16 konteynerin 7'si :latest tag ile çalışıyor. Beklenmeyen
      güncelleme ile uygulama kırılabilir.
    impact: Production kesintisi, uyumsuzluk
    probability: YÜKSEK
    mitigation: |
      1. Her container için sabit versiyon belirle
      2. docker-compose.yml'de tag'leri sabitle
      3. Update prosedürü oluştur
    status: OPEN
    owner: jeff

  - id: RISK-006
    title: Secret envanteri eksik
    severity: HIGH
    category: Security
    description: |
      8 env secret'ı metadata olarak tespit edildi. Ancak
      git history, backup dosyaları, loglar ve config dosyaları
      için sızıntı taraması yapılmadı.
    impact: Secret sızıntısı, yetkisiz erişim
    probability: ORTA
    mitigation: |
      1. git log'da secret taraması yap
      2. Backup dosyalarını kontrol et
      3. Log dosyalarını tara
      4. Sızıntı bulursan rotate et
    status: OPEN
    owner: jeff

  - id: RISK-007
    title: Tek sunucuda çoklu kritik servis
    severity: HIGH
    category: Architecture
    description: |
      HM Panel, n8n, Coolify, ErgeneAI, Dograh, Beszel ve
      Hermes VM tek sunucuda çalışıyor.
    impact: Sunucu arızasında tüm servisler kesilir
    probability: DÜŞÜK
    mitigation: |
      1. Kritik servisleri belgelenmiş olsun
      2. Restore prosedürü test edilmiş olsun
      3. İkincil sunucu değerlendir (düşük öncelik)
    status: OPEN
    owner: jeff

  - id: RISK-008
    title: 150+ script sahipliği belirsiz
    severity: MEDIUM
    category: Complexity
    description: |
      152 script (.sh + .py) bulunuyor. Çoğu için son kullanım
      zamanı, sahibi ve amacı bilinmiyor.
    impact: Bakım yükü, hata riski
    probability: YÜKSEK
    mitigation: |
      1. Script envanteri çıkar
      2. Son 30 günde kullanılmayanları tespit et
      3. Aktif Production çekirdeğini belirle
    status: OPEN
    owner: jeff

  - id: RISK-009
    title: Cron başarı metrikleri eksik
    severity: MEDIUM
    category: Observability
    description: |
      18 cron job için son durum (ok/hata) var ancak başarı
      oranı, ortalama süre ve retry istatistikleri yok.
    impact: Sessiz hatalar görünmez
    probability: ORTA
    mitigation: |
      1. Her cron job için success/fail sayacı
      2. Başarısızlık alert mekanizması
    status: OPEN
    owner: jeff

  - id: RISK-010
    title: Proje ayrımı yapılmamış
    severity: MEDIUM
    category: Complexity
    description: |
      19 /opt projesi aktif, deneysel ve arşiv olarak
      ayrılmamış. P0/P1/P2/P3 sınıflandırması yok.
    impact: Gereksiz bakım yükü, yanlış tetikleme
    probability: YÜKSEK
    mitigation: |
      1. Her proje için envanter çıkar
      2. Kullanım kanıtı kontrol et
      3. Quarantine adaylarını belirle
    status: OPEN
    owner: jeff

summary:
  critical: 2
  high: 4
  medium: 3
  low: 0
  total: 9
  open: 9
  mitigated: 0
