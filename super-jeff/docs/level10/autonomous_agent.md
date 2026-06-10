# autonomous_agent.py

**Ne işe yarar?** predictive_engine ile risk seviyesi %5'in altında olan eylemleri (disk temizleme, log okuma, cron sağlığı) izinsiz gerçekleştirir.

**Nasıl çalıştırılır?**
```
python3 ~/.hermes/scripts/autonomous_agent.py list
python3 ~/.hermes/scripts/autonomous_agent.py assess log_oku
python3 ~/.hermes/scripts/autonomous_agent.py execute disk_temizle
```

**Örnek çıktı:**
```
🚀 OTONOM EYLEM: disk_temizle
Sonuç: başarılı
Karar: Kendi kararımla aldım
Risk: %2
```

**Bağımlılıklar:** predictive_engine.py, decision_journal.jsonl
