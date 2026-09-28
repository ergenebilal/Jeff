# Production Readiness Gate
# Generated: 2026-08-17T14:15:00+03:00
# Mod: AUDIT_ONLY

gate_status: NOT_PASSED
readiness_pct: 10

gates:
  - id: GATE-01
    name: Sunucu dışı yedek doğrulanmış
    status: ❌ NOT_VERIFIED
    detail: jeff-backup.tar.gz mevcut ama kapsam/restore doğrulanmamış
    blocking: true

  - id: GATE-02
    name: Kritik varlıklar restore testinden geçmiş
    status: ❌ NOT_TESTED
    detail: Hiçbir restore testi yapılmamış
    blocking: true

  - id: GATE-03
    name: RAM ve Docker baseline tamamlandı
    status: ⚠️ PARTIAL
    detail: Tek anlık ölçüm var, 24 saatlik seri gerekli
    blocking: false

  - id: GATE-04
    name: OOM ve kaynak alarmları çalışıyor
    status: ❌ NOT_CONFIGURED
    detail: Beszel monitoring var ama OOM alarmı tanımlanmamış
    blocking: false

  - id: GATE-05
    name: Kritik portların maruziyeti doğrulanmış
    status: ⚠️ PARTIAL
    detail: UFW var ama Docker port bypass riski tespit edildi
    blocking: true

  - id: GATE-06
    name: Secret sızıntısı bulunmuyor veya rotate edilmiş
    status: ❌ NOT_SCANNED
    detail: Git history, backup ve log taraması yapılmamış
    blocking: true

  - id: GATE-07
    name: Agent yetkileri sınıflandırılmış
    status: ❌ NOT_CLASSIFIED
    detail: L0-L5 sınıflandırması belgelenmemiş
    blocking: false

  - id: GATE-08
    name: P0/P1 production çekirdeği belgelenmiş
    status: ⚠️ PARTIAL
    detail: Bu raporda belgelendi (01-asset-inventory.yaml)
    blocking: false

  - id: GATE-09
    name: Cron başarısızlıkları görünür
    status: ⚠️ PARTIAL
    detail: Son durum var ama success/fail oranı yok
    blocking: false

  - id: GATE-10
    name: Geri dönüş planı test edilmiş
    status: ❌ NOT_TESTED
    detail: Rollback planı yazıldı ama test edilmedi
    blocking: true

blocking_gates: 5
non_blocking_gates: 5
passed_gates: 0

next_steps:
  priority_1:
    - action: Dış yedek durumunu doğrula
      owner: jeff
      estimated_time: 30min

    - action: jeff-backup.tar.gz kapsam listesini çıkar
      owner: jeff
      estimated_time: 15min

    - action: Docker port bypass testi yap (nmap)
      owner: jeff
      estimated_time: 15min

    - action: Git history secret taraması
      owner: jeff
      estimated_time: 30min

  priority_2:
    - action: 24 saatlik RAM baseline başlat
      owner: jeff
      estimated_time: 5min (otomatik)

    - action: ps_mem ile RAM dağılımı ölç
      owner: jeff
      estimated_time: 10min

    - action: PostgreSQL DB boyutunu ölç
      owner: jeff
      estimated_time: 5min

  priority_3:
    - action: Quarantine adaylarını taşı
      owner: jeff + approval
      estimated_time: 1saat

    - action: :latest tag'leri sabitle
      owner: jeff + approval
      estimated_time: 30min

    - action: Privileged flag kaldır
      owner: jeff + approval
      estimated_time: 30min
