# Sade Dil Kuralı — v1.2 (10.09.2026 güncellemesi)

**Tetikleyici (v1.1):** Kullanıcı "Daha sade bir dil ile anlat" dedi. Fikir #1 EU AI Act'i karmaşık teknik dille anlatınca anlaşılmadı.
**Tetikleyici (v1.2):** Bilal "bundan sonra ben sana teknik dil içeren bir prompt versem bile sen bana işlemlerin sonunda sade bir dille açıklayacaksın" dedi.

## 🔴 ANA KURAL (v1.2) — DEĞİŞMEZ

**Prompt ne kadar teknik olursa olsun, her işin SONUNDA sade dil özeti verilir.**

Bilal teknik dilde yazmayı sever ("read-only audit", "surgical change", "root cause", "production kanıtı", "smoke test"). **Bu, cevabın da teknik olması gerektiği anlamına GELMEZ.** Teknik prompt = teknik *görev*, sade *cevap*.

### Zorunlu kapanış bloğu (her işin sonunda)
Şu 3 soruya jargonsuz, sade Türkçeyle cevap ver:
1. **Ne yaptım?** — normal insan diliyle, 2-3 cümle
2. **Ne buldum?** — sayı varsa sadeleştir ("₺258-1.050" → "en ucuzu 258 lira")
3. **Senden ne istiyorum?** — tek net adım, ya da "senin bir şey yapmana gerek yok"

### Yasaklı kelimeler (kapanış bloğunda)
`hook`, `enforcement`, `sys.modules`, `root cause`, `verdict`, `blocked=true`, `dry_run`, `latency`, `smoke test`, `audit`, `migration`, `idempotent`, `DNS`, `TLS`, `payload`, `endpoint` — bunlar **detay bölümünde** kalır, **kapanışta geçmez**.

Çeviri örnekleri:
- ❌ "hook.py'ye dry_run early-return eklendi, enforcement artık tetiklenmiyor"
- ✅ "Bir güvenlik kontrolü vardı, mesajlarımı yanlış yere kilitliyordu. Düzelttim, artık kilitlenmiyor."
- ❌ "7 domain DNS'de çözümlenmiyor"
- ✅ "7 işletmenin internet adresi artık yok — müşteri tıklasa sayfa açılmıyor."
- ❌ "ADE full-LLM 12dk 41sn'de tamamlanmadı"
- ✅ "Bir analiz aracı var; 12 dakikada bitmedi, yani şu an kullanılamaz durumda."

### Yapı kuralı
- **Detay üstte, sade özet EN SONDA.** Baştan sade yazıp detayı hiç vermemek de hata — Bilal detayı da ister.
- Sade özet **en az 3 cümle** olsun; "özetle düzelttim" gibi tek satır kuru kapanış yeterli değil.
- Sade özetten sonra **yeni teknik başlık açma** — iş orada biter.

## Fikir anlatımı (v1.1 — hâlâ geçerli)
- Önce **"Ne oldu? Neden para eder? Ne satıyoruz? Kime satıyoruz?"** 4 sorusuna 1'er cümlede cevap ver.
- Teknik jargon (C2PA, watermark, stateless, MCP) ilk paragrafta YASAK — en alta "Teknik not" olarak taşı.
- Rakamı sadeleştir: "$990 = ~50.000 TL = 10 haftalık birikim" gibi somutlaştır.
- Uzun tablo yerine 4 satırlık sade tablo kullan.

## Anti-pattern (v1.1)
- ❌ "EU AI Act Madde 50 şeffaflık yükümlülükleri 2 Ağustos'ta yürürlüğe girdi, makine-okunur işaretleme..."
- ✅ "Avrupa yeni yasa çıkardı. Chatbot 'ben AI'ım' demek zorunda, uymayana 15 Milyon € ceza."

## Anti-pattern (v1.2)
- ❌ 60 satır teknik rapor verip tek satır "özet: tamam" yazmak
- ❌ Sade özeti **başa** koyup detayı silmek (Bilal detayı da ister)
- ❌ Sade özete "yani aslında..." diye teknik parantez sıkıştırmak

**Uygulama:** Fikir sunumu, teklif metni, DM şablonu, rapor özeti, **ve her işin kapanışı** — sade dil ilk 30 saniyede anlaşılmalı.
