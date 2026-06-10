# swarm_orchestrator.py

**Ne işe yarar?** Ana Jeff, bir görevi alt görevlere böler. Her alt görev için yeni bir Jeff instance'ı (kopya) oluşturup paralel çalıştırır (subprocess ile).

**Nasıl çalıştırılır?**
```
python3 ~/.hermes/scripts/swarm_orchestrator.py decompose "E-ticaret analizi"
python3 ~/.hermes/scripts/swarm_orchestrator.py run "Sosyal medya planı"
python3 ~/.hermes/scripts/swarm_orchestrator.py run "Analiz" -t "Veri topla" "İşle" "Raporla"
```

**Örnek çıktı:**
```
🐝 SWARM ÇALIŞTIRILDI
Swarm ID: task_2336_4821
Alt görev: 3 | Başarılı: 3
  ✅ jeff_kopya_1 — görev tamamlandı
  ✅ jeff_kopya_2 — görev tamamlandı
  ✅ jeff_kopya_3 — görev tamamlandı
```

**Bağımlılıklar:** subprocess
