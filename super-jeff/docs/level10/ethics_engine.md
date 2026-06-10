# ethics_engine.py

**Ne işe yarar?** Her karardan önce 4 prensibe göre etik sorgulama: Zarar Verme, Adil Olma, Gizliliğe Saygı, Dürüst Olma. Etik dışı eylemlere alternatif önerir.

**Nasıl çalıştırılır?**
```
python3 ~/.hermes/scripts/ethics_engine.py check "Gumroad ürünlerini güncelle"
python3 ~/.hermes/scripts/ethics_engine.py check "rakibin verilerini çal"
python3 ~/.hermes/scripts/ethics_engine.py alternative "rakibin verilerini çal"
```

**Örnek çıktı:**
```
✅ ETİK (skor: %100)
🚨 ETİK DEĞİL (skor: %20)
Prensip: Zarar Verme: ⚠️ %20 | Adil Olma: ✅ %100
```

**Bağımlılıklar:** ethics_log.jsonl
