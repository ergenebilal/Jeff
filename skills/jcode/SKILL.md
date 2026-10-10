---
name: jcode
description: >-
  Jeff -> jcode kodlama delegasyon protokolü.
  jcode (Rust AI coding agent, v0.78.1) birincil ağır kodlama ve refactoring aracıdır.
  OpenRouter altyapısı üzerinden çalışır (nvidia/nemotron-3.5-lightning:free).
  Kod yazma, çok dosyalı refactor, test çalıştırma ve hata ayıklama için terminal üzerinden çağrılır.
category: coding
---

# Jeff -> JCode Delegasyon Protokolü

## 🔴 ROL AYRIMI (Orchestrator vs Executor)

- **Jeff (Orchestrator / Beyin):** Strateji belirler, planlar, mimariyi yönetir.
- **JCode (Heavy Coder / Kodlama Motoru):** Rust tabanlı ultra hızlı CLI kodlama ajanıdır. Kod yazar, derler, refactor yapar.

## ✅ ÇALIŞIYOR — v0.84.0 (12.09 gece, gerçek görev kanıtıyla)
```bash
/home/hermes/.local/bin/jcode --provider openai-compatible -m deepseek-v4.1-flash --quiet run "GÖREV"
```
- **Kritik çözüm:** v0.78.1 OpenCode Go'nun yapıştırdığı `x-opencode-session` başlığını gönderemiyordu → 400 MissingSessionID (aylık kota 429'u değil, protokol uyumsuzluğuydu). `jcode update` ile v0.84.0'a çıkarıldı; sorun tamamen çözüldü. jcode güncel tutulmalı (JCODE_NO_AUTO_UPDATE çevirme).
- varsayılan: config.toml `[provider] default_provider="openai-compatible"`, `default_model="deepseek-v4.1-flash"` (Bilal onaylı rota: jcode=DS 4.1 Flash).
- Çalışma kanıtı (12.09 21:40): gerçek görev — inputs.txt+hesaplayici.py üretti, çalıştırdı, kendi virgül-bindirme hatasını yakayıp düzeltti. Cache-read %97, upload ~34k, hızlı.
- `run` foreground'da 120-180sn sessiz timeout vera bilir → HER ZAMAN background (terminal background=true, log dosyasına yaz, sonra poll).
- opencode-go native provider hâlâ header koymuyor — KULLANMA, openai-compatible yolu tek sağlam hat.


## Kanıtla kapanan görev yolu (24 Eylül 2026)

Kodlama görevini mevcut `terminal` aracıyla aşağıdaki yürütücüye ver.
Görevin hedefini, gerçek mutlak çalışma dizinini ve projeye ait doğrulama
komutunu çağrıdan önce belirle. Test komutu yalnız `echo` veya başarı metni
üreten bir komut olamaz; ilgili davranışı sınayan mevcut proje testini kullan.

```sh
python3 /home/hermes/.hermes/skills/jcode/scripts/verified_coding.py --workspace /mutlak/proje --task-id benzersiz-gorev-kimligi --goal 'İstenen değişiklik ve tamamlanma koşulu' --test-argv '["python3", "-m", "unittest", "discover"]'
```

Uzun görevlerde `terminal(background=true)` kullan ve aynı terminal işinin
sonucunu bekle. Yürütücü mevcut jcode sağlayıcı/model rotasını korur; kodlayıcı
ve test gerçek çalışma dizininde ayrı süreçler olarak çalışır. Alt adımlar,
hedef, çıkış kodları ve ham test çıktısı `.cybergene-tasks/` altında saklanır.
Yalnız `status=VERIFIED`, kodlayıcı exit=0 ve test exit=0 birlikteyse tamamlandı
de. Kapanışta test argv, çalışma dizini ve ilgili ham test satırını göster.
ERROR/TIMEOUT/INTERRUPTED/IN_PROGRESS durumlarını başarı diye özetleme.
Aynı task-id aynı sözleşmeyle tekrar çağrıldığında kayıt okunur; tekrar kod
yürütülmez. Düzeltme denemesi için önce eski sonucu incele, yeni görev kimliği
kullan ve önceki kimliği hedef açıklamasında belirt.

Pablo için mevcut `alfred --request-id <kimlik> ...` aracını kullan.
`alfred status <kimlik>` yürütmeyi yinelemeden sonucu sorgular. APPROVAL_REQUIRED,
BLOCKED, OFFLINE, TIMEOUT ve IN_PROGRESS tamamlanmış iş değildir. Zaman aşımında
aynı eylemi yeni kimlikle otomatik gönderme; önce kayıtlı kimliği uzlaştır.
Onay yalnız sahibin tam görev içeriğini onaylayan Telegram düğmesiyle verilir.
Servis restartı, token yenileme, firewall ve canlı GUI testleri için mevcut
insan onayı sınırlarını koru; bu yürütücü bunlara yeni yetki vermez.

`--engine aider` mevcut Aider CLI ve proxy rotasını kullanır; Aider ile başlanmış
işi otomatik olarak jcode aracına taşıma. Varsayılan `--engine jcode`, yukarıdaki
mevcut jcode rotasıdır. İki araç arasında otomatik delegasyon varsayma.

Alfred request-id/status sözleşmesi, Pablo protocol_version=2 ile birlikte
etkinleştirilmelidir. İstemci `alfred_tool.py.next` olarak hazırlanmışken mevcut
CLI üzerinde bu yeni bayrakları kullanma; koordineli aktivasyon onayını bekle.
