# accelerated_learning.py

**Ne işe yarar?** meta_learner'ın planını uygular. Başarısız adımları tespit edip planı dinamik olarak günceller.

**Nasıl çalıştırılır?**
```
python3 ~/.hermes/scripts/accelerated_learning.py simulate "Instagram API"
python3 ~/.hermes/scripts/accelerated_learning.py execute "Instagram API" --real
```

**Örnek çıktı:**
```
🚀 HIZLANDIRILMIŞ ÖĞRENME SİMÜLASYONU
Skill: Instagram API
Normal süre: 30dk → Meta: 24dk
Kazanım: %20
```

**Bağımlılıklar:** meta_learner.py, learning.py
