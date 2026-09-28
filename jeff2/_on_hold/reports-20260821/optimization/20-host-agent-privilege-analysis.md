# 20-Host-Agent-Privilege-Analysis.md
**Spec:** JEFF-OPT-MASTER-001 Phase 3
**Tarih:** 2026-08-17 15:00 UTC+3
**Operator:** Jeff

---

## Executive Summary

**Önceki rapor (09-container-security-report.yaml) hmpanel-host-agent'ı `privileged=true` ve `pid=host` olarak raporlamıştır. Bu DOĞRU DEĞİLDİR.**

Mevcut durum:
- `Privileged: false`
- `PidMode: ""` (boş — host PID namespace'de değil)
- `CapAdd: None`
- `CapDrop: None`
- `Devices: None`
- Mount: `/sys → /host/sys (read-only)`, `/proc → /host/proc (read-only)`
- Command: `sleep infinity`
- Image: `alpine` (pinned SHA256)

---

## 1. Mevcut Durum Analizi

### Container Config

| Alan | Değer | Risk |
|------|-------|------|
| Privileged | false | ✅ GÜVENLİ |
| PidMode | "" (empty) | ✅ GÜVENLİ |
| NetworkMode | hmpanel_network | ✅ GÜVENLİ |
| CapAdd | None | ✅ GÜVENLİ |
| CapDrop | None | ✅ Nötr |
| Devices | None | ✅ GÜVENLİ |
| SecurityOpt | None | ✅ Nötr |
| ReadonlyRootfs | false | ⚠️ DÜŞÜK |
| User | root (default) | ⚠️ ORTA |
| Entrypoint | None | — |
| Cmd | ["sleep", "infinity"] | — |

### Mount Analizi

| Mount | Type | Source | Destination | RW | Risk |
|-------|------|--------|-------------|-----|------|
| 1 | bind | /sys | /host/sys | false | ⚠️ ORTA |
| 2 | bind | /proc | /host/proc | false | ⚠️ ORTA |

**Risk Değerlendirmesi:**
- `/sys` (read-only): Host kernel parametrelerine erişim. Container escape durumunda bilgi sızıntısı riski.
- `/proc` (read-only): Process bilgilerine erişim. Düşük risk ama host bilgisi sızabilir.
- Her ikisi de read-only — yazma yok, bu iyi.

### Container Amacı

HM Panel host-agent, panel'in host üzerindeki kaynakları izlemesi için bir sidecar container'ıdır. `sleep infinity` ile çalışıyor — gerçek bir agent process'i çalıştırmıyor. Muhtemelen:
- HM Panel dashboard'unda host bilgilerini göstermek için
- Veya henüz aktif olmayan bir özellik için beklemede

---

## 2. Gerçek Fonksiyon Gereksinimleri

| Fonksiyon | Gerekli mi? | Mevcut | Önerülen |
|-----------|-------------|--------|----------|
| Host CPU/RAM izleme | Evet (muhtemelen) | /proc, /sys mount | Korunabilir (read-only) |
| Disk izleme | Evet (muhtemelen) | /proc, /sys mount | Korunabilir |
| Network izleme | Bilinmiyor | — | — |
| Docker erişim | Hayır | Yok | ✅ |
| Process yönetimi | Hayır | Yok | ✅ |
| Dosya yazma | Hayır | Yok | ✅ |

---

## 3. Test Ortamı Denemesi

Privileged kaldırma denemesi GEREKMEZ çünkü zaten `privileged=false`.

Mevcut durum zaten güvenli. Önceki raporun hatalı olduğu doğrulanmıştır.

---

## 4. Minimum Capability Listesi

Mevcut durumda_capAdd=None ve CapDrop=None. Container zaten ek capability istemiyor.

Eğer izleme için gerçek bir agent process'i çalıştırılacaksa gerekli minimum:

```
cap_add:
  - SYS_PTRACE     # /proc erişimi için (read-only mount ile birlikte)
```

Ancak mevcut `sleep infinity` durumunda hiçbir capability gerekmez.

---

## 5. Öneriler

| # | Öneri | Seviye | Onay Gerekir mi? |
|---|-------|--------|-------------------|
| 1 | Mevcut durum kabul edilebilir | LOW | Hayır |
| 2 | ReadonlyRootfs: true yap | LOW | Hayır |
| 3 | User: non-root yap (eğer mümkünse) | MEDIUM | Evet |
| 4 | /sys ve /proc mount'u kaldır (eğer izleme gerekmiyorsa) | MEDIUM | Evet |
| 5 | Container'ı tamamen kaldır (eğer işe yaramıyorsa) | HIGH | Evet |

---

## 6. Düzeltme

Önceki raporun (09-container-security-report.yaml) `hmpanel-host-agent` satırı güncellenmelidir:

**Önceki (HATALI):**
```yaml
- name: hmpanel-host-agent
  privileged: true
  pid_mode: host
  risk: CRITICAL
```

**Güncel (DOĞRU):**
```yaml
- name: hmpanel-host-agent
  privileged: false
  pid_mode: ""
  risk: LOW
  finding: |
    Container privileged DEĞİL. Sadece /sys ve /proc read-only mount var.
    sleep infinity ile çalışıyor — aktif agent process'i yok.
```

---

*Bu rapor 20-host-agent-privilege-analysis.md olarak adlandırılmıştır.*
