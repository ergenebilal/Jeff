# Pipeline Health Check — Content Delivery Diagnostics

> Herhangi bir otomatik içerik pipeline'ında (IG, Twitter, blog) delivery sorunlarını teşhis için.
> "İçerik tekrarlıyor", "post gitmiyor", "pipeline çalışmıyor" şikayetlerinde buraya bak.

## 1. Credential / Token Varlığı

Pipeline'ın hedef platforma (Telegram, API, SMTP) içerik gönderebilmesi için credential dosyaları var olmalıdır. **Credential kaybolursa pipeline sessizce başarısız olur:**

- ✅ İçerik üretilir, QA geçer, output klasörüne yazılır
- ❌ Hedefe hiçbir şey gönderilmez
- ❌ Pipeline log'unda "Sent:" satırı görünmez
- ❌ State tracker güncellenmez

**Kontrol:**
```bash
# IG Bot Token
python3 -c "
import os
tf = os.path.expanduser('~/.hermes/secrets/ig_bot_token.txt')
if os.path.exists(tf): print(f'✅ IG bot token: {os.path.getsize(tf)} bytes')
else: print('❌ IG bot token eksik')
"
```

## 2. Cron Job Kaydı

Pipeline cron'u skill'de tanımlı olabilir ama sistemde kayıtlı olmayabilir.

**Kontrol:** Cron job'un `cronjob action=list` çıktısında göründüğünü, `last_status`'un "ok" olduğunu, `enabled`'ın true olduğunu doğrula.

## 3. Delivery vs Generation Gap

En sessiz hata: içerik üretilir, onaylanır, output klasörüne yazılır — ama delivery başarısız olur.

**Belirtiler:**
- Output/approved klasörü slide/post dolu
- Log'da "Sent:" satırı yok veya çok az
- State tracker'daki `total_sent` düşük
- Art arda "Already sent today, skipping" log mesajları (state güncel değil)

**Teşhis:**
```bash
cd /opt/hermes/instagram-pipeline  # veya ilgili pipeline dizini
APPROVED=$(ls output/approved/*.png 2>/dev/null | wc -l)
LOG_SENT=$(grep -c 'Sent:' output/logs/daily_pipeline.log 2>/dev/null || echo "0")
echo "Approved: $APPROVED | Log Sent: $LOG_SENT"
python3 -c "
import json
try:
    d = json.load(open('output/state/post_tracker.json'))
    print(f'Tracker: {d}')
except: print('Tracker yok')
"
```

## 4. Content Plan Exhaustion

Sabit sayıda post'u olan bir pipeline, QA rejection oranı yüksekse hızla tükenir ve başa sarar.

**Belirti:** Kullanıcı "postlar kendini tekrar ediyor" dediğinde ilk kontrol:
```bash
python3 -c "
from daily_pipeline import CONTENT_PLAN
print(f'Plan: {len(CONTENT_PLAN)} post')
for p in CONTENT_PLAN:
    print(f'  Post {p[\"id\"]}: {p[\"theme\"]}')
"
# Tracker kontrolü
python3 -c "
import json
d = json.load(open('output/state/post_tracker.json'))
print(f'Tracker: {d}')
if d[\"last_post_id\"] >= 12:
    print('⚠️ Content plan sonuna gelinmis veya asilmis')
"
```

**Çözüm:**
1. Content plan'ı genişlet (12→20+ post)
2. Track rotasyonu ekle (sorun→çözüm / eğitim/rehber)
3. Aynı temayı farklı açılardan işle (acı → fırsat → istatistik → hikaye)

## 5. Batch Kurtarma

Birikmiş onaylanmış içeriği göndermek için batch mod:
```bash
cd /opt/hermes/instagram-pipeline  # pipeline dizini
python3 daily_pipeline.py --batch 4,5,6,7,8
```

Batch mode state güncellemez. Sonrasında manuel güncelle:
```bash
python3 -c "
import json
d = json.load(open('output/state/post_tracker.json'))
d['total_sent'] = 8  # batch'te gönderilen son post ID'si
d['last_post_id'] = 8
json.dump(d, open('output/state/post_tracker.json', 'w'), indent=2)
"
```
