# Subagent Delegasyon SOP

Jeff teknik işleri worker subagent'lara devrederken bu kuralları takip eder.

---

## 1. Delegasyon Akışı

1. Jeff görevi tanımlar → `delegate_task` çağırır
2. Jeff beklemez, hemen başka işe geçer (arka planda çalışır)
3. Subagent dönünce Jeff çıktıyı denetler
4. Eğer 45 saniye içinde dönmezse → timeout kuralı
5. Eğer hata dönerse → retry veya fallback

## 2. Timeout Kuralı

- **Bekleme süresi:** 120 saniye (`child_timeout_seconds: 120` — Hermes config'inde hard cap)
- **Subagent çalışıyor kontrolü:** Jeff 120sn içinde dönüş gelmezse timeout kabul eder
- **120sn geçtiyse:** Retry kuralına geç
- **Not:** 120sn üzeri işler için subagent değil, cron job veya OpenCode kullanılır

## 3. Retry Kuralı

- **1 retry** yapılır. 2. kez de başarısız olursa fallback'e geç.
- Retry'da çağrı aynen tekrarlanır (aynı goal, aynı context).
- Retry sebebi her zaman raporda yazılır.
- Retry sayısı asla 1'i geçmez. 2 kez aynı hatayı yapmak sistemin sınırıdır.

## 4. Fallback Kuralı

**Fallback'e geçme koşulları (TÜMÜ aynı anda):**
1. Subagent 2 kez başarısız oldu (anlık hata, timeout, boş dönüş veya yarım dönüş)
2. İş kritik: başka bir bloğu açıyor, zaman kaybı kabul edilemez
3. Jeff yapabilir: iş Jeff'in tool setinde, kod yazma gerektirmiyor

**Fallback'te Jeff yapmaz:**
- Subagent'tan daha hızlı yapamayacağı işler (10+ dosya okuma)
- Kod yazma gerektiren işler (bunun için OpenCode var)
- Dış API'ye bağımlı işler (API key gerekiyorsa subagent da yapamaz)

**Fallback raporu şu formatla yazılır:**
```
🔄 Fallback: [iş adı]
Neden: [hata türü + kaç deneme]
Süre: [toplam geçen süre]
Çözüm: [Jeff ne yaptı]
```

## 5. Hata Türleri ve Davranış

| Hata | Ne yapılır? | Retry? | Fallback? |
|------|------------|:------:|:---------:|
| **HTTP 404** | ~~Subagent çağrısı yerine ulaşamadı~~ ✅ **09.07.2026 — ÇÖZÜLDÜ.** Kök neden: config'de tanımsız provider. Fix: delegation override'ları kaldırıldı. Subagent artık ana provider'ı miras alıyor. | ❌ Artık gerekmez | Hayır, 404 kalıcı çözüldü |
| **Timeout** | 45sn içinde dönüş yok | ✅ 1 kez | Evet, ikisinde de timeout ise |
| **Boş dönüş** | Subagent döndü ama içerik yok | ✅ 1 kez | Evet |
| **Yarım dönüş** | Çıktı var ama anlamsız/kesik | ❌ Retry yapılmaz | Hayır, sorunu anlamak için Jeff analiz eder |
| **Provider hatası** | Model provider geçici arıza | ✅ 1 kez | Evet |
| **Tool hatası** | Subagent tool çağıramadı | ❌ Retry yapılmaz | Hayır, altyapı sorunu ayrı ameliyat |

## 6. Jeff'in Yetki Sınırı

**Jeff işi kendi alabilir (fallback):**
- Subagent 2 kez başarısız
- İş kritik (başka bloğu açıyor)
- Jeff yapabilir (tool setinde)
- Süre kaybı kabul edilemez

**Jeff işi asla kendisi yapmaz:**
- Kod yazma gerekiyorsa (OpenCode'a gitmeli)
- 3+ dosyaya birden dokunulacaksa
- İş sadece subagent'ın yapabileceği bir tool gerektiriyorsa
- İş basit ve tekrarlanabilir değilse (SOP'a dönüşmemişse)

## 7. Raporlama Kuralı

Her delegasyon şunları içerir:
- Hangi iş devredildi
- Subagent başarılı mı (✅/❌)
- Ne kadar sürdü
- Retry yapıldıysa kaç kez
- Fallback yapıldıysa neden

Bu bilgi feed'e yazılır ve Kabine raporunda görünür.

## 8. Başarı Ölçüsü

Subagent sistemi başarılıdır eğer:
- 10 delegasyondan en az 8'i başarılı (başarı oranı ≥ %80)
- Ortalama dönüş süresi ≤ 10 saniye
- Fallback oranı ≤ %20 (10 delegasyonda en fazla 2 fallback)
- Jeff kendi üstüne aldığı iş sayısı ≤ fallback sayısı (yani her fallback'te işi Jeff alabilir ama tercih edilmez)
