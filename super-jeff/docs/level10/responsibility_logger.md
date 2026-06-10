# responsibility_logger.py

**Ne işe yarar?** Otonom alınan her kararın nedenini, alternatiflerini ve beklenen sonucunu kaydeder. Hatalı kararlarda "Şef, yanlış karar verdim" diyerek özür diler ve learning.py'ye ders kaydeder.

**Nasıl çalıştırılır?**
```
python3 ~/.hermes/scripts/responsibility_logger.py log disk_temizle --risk 0.03
python3 ~/.hermes/scripts/responsibility_logger.py report disk_temizle --success
python3 ~/.hermes/scripts/responsibility_logger.py stats
```

**Örnek çıktı:**
```
📊 OTONOM KARAR İSTATİSTİKLERİ
Toplam: 5 | Başarılı: 4 | Başarısız: 1
Başarı oranı: %80
```

**Bağımlılıklar:** complex_mood_engine.py, learning.py
