# value_based_filter.py

**Ne işe yarar?** Kullanıcıdan gelen komutları değer süzgecinden geçirir. Etik dışı komutları "Yapamam Şef" diyerek reddeder ve alternatif sunar.

**Nasıl çalıştırılır?**
```
python3 ~/.hermes/scripts/value_based_filter.py evaluate "Yeni Instagram post taslağı hazırla"
python3 ~/.hermes/scripts/value_based_filter.py evaluate "Rakibin hakkında kötü yorum yaz"
python3 ~/.hermes/scripts/value_based_filter.py history
```

**Örnek çıktı:**
```
🚨 RED: Yapamam, bu komut etik prensiplerimle çelişiyor.
💡 Alternatif: Kendi ürününü geliştir
```

**Bağımlılıklar:** ethics_engine.py
