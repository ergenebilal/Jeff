# CYBERGENE SYSTEM-1 KARAR MOTORU (JEV MİMARİSİ)

## 🎯 Ne Zaman Kullanılır
- Müşteri mesajı, lead sınıflandırması, güvenlik kapısı veya hızlı yönlendirmelerde paragraf/metin üretmeden milisaniyelik tip korumalı (typed) karar gerektiğinde.
- Devasa LLM'lerin (System-2) sırtındaki gereksiz `if-else` yükünü almak istendiğinde.

## 🛠️ Üç Temel Primitif (The 3 Primitives)

1. **`choice(state, question, options)`:**  
   Verilen durum context'ine göre belirlenen seçeneklerden tam olarak bir tanesini karar ve güven skoruyla (confidence) seçer.
   
2. **`boolean(state, statement)`:**  
   Bir iddianın veya durumun Doğru (True) mi Yanlış (False) mi olduğunu milisaniyeler içinde doğrular.

3. **`score(state, rubric)`:**  
   Belirlenen kriterlere (rubric) göre durumu 1-10 arasında skorlar.

## ⚙️ Kod Yolu & Kullanım

```python
from system1_decision_engine import System1DecisionEngine

engine = System1DecisionEngine()

# Choice
decision = engine.choice(state={"client": "X"}, question="Action?", options=["OPT_A", "OPT_B"])

# Boolean
is_safe = engine.boolean(state={"msg": "text"}, statement="Is safe?")
```

## 🛠️ Pitfalls (Önemli Tuzaklar)
- **Generative Text Bekleme:** System-1 modelleri metin/paragraf üretmek için kullanılmaz. Çıktı doğrudan JSON/Typed veridir.
- **System-2 ile Ayrım:** Derin düşünme, kod yazımı ve metin taslağı üretimi System-2 (Claude Sonnet 4.6 / Opus 4.6) modellerine yönlendirilmelidir.
