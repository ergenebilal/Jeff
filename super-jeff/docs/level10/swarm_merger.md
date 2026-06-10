# swarm_merger.py

**Ne işe yarar?** Tüm alt Jeff'lerin çıktılarını toplar, birleştirilmiş rapor haline getirir ve ana Jeff'e sunar.

**Nasıl çalıştırılır?**
```
python3 ~/.hermes/scripts/swarm_merger.py collect <swarm_id>
python3 ~/.hermes/scripts/swarm_merger.py merge <swarm_id>
python3 ~/.hermes/scripts/swarm_merger.py list
python3 ~/.hermes/scripts/swarm_merger.py report <swarm_id>
```

**Örnek çıktı:**
```
🔗 SWARM BİRLEŞTİRME RAPORU
Swarm ID: task_2336_4821
Agent: 3 | Başarılı: 3/3 | Başarı: %100
```

**Bağımlılıklar:** swarm_orchestrator.py
