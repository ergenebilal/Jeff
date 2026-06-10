# meta_learner.py

**Ne işe yarar?** Yeni bir skill verildiğinde geçmiş episodic_memory ve semantic_memory'yi tarayıp benzer skill'lerin nasıl öğrenildiğini analiz eder. Bir "öğrenme planı" oluşturur.

**Nasıl çalıştırılır?**
```
python3 ~/.hermes/scripts/meta_learner.py plan "Instagram API"
python3 ~/.hermes/scripts/meta_learner.py compare "Instagram API"
```

**Örnek çıktı:**
```
📚 ÖĞRENME PLANI: Instagram API
⏱️  Normal süre: 30dk → Meta: 24dk
⚡ Hızlanma: %20 daha hızlı
📋 12 adımlı plan
```

**Bağımlılıklar:** learning.py, episodic_memory.jsonl, semantic_knowledge.json
