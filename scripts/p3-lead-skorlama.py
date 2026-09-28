#!/usr/bin/env python3
"""
P3 — Zero-shot Lead Skorlama
ICP'ye göre lead'leri otomatik sınıflandır: hot/warm/cold
"""
import os, sys, json, numpy as np
from transformers import AutoTokenizer, AutoModel
import torch

# Embedding modeli (Türkçe dahil)
model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

def embed(text):
    inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
    attention_mask = inputs['attention_mask']
    token_embeddings = outputs.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    embedding = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return embedding[0].numpy()

def cosine_similarity(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# ICP Kategorileri
ICP_CATEGORIES = {
    "hot": "Bu işletme dijital dönüşüme açık, AI otomasyona ihtiyacı var, bütçesi var, karar vericiye kolay ulaşılır",
    "warm": "Bu işletme dijital araçlar kullanıyor ama AI otomasyona geçmemiş, potansiyeli var",
    "cold": "Bu işletme küçük, bütçesi kısıtlı, dijital dönüşüme kapalı veya henüz hazır değil"
}

def score_lead(lead_name, lead_category, lead_city, lead_notes=""):
    """Bir lead'in ICP skorunu hesapla"""
    lead_text = f"{lead_name} {lead_category} {lead_city} {lead_notes}"
    lead_vec = embed(lead_text[:500])
    
    scores = {}
    for label, desc in ICP_CATEGORIES.items():
        cat_vec = embed(desc)
        scores[label] = cosine_similarity(lead_vec, cat_vec)
    
    # Normalize et
    total = sum(scores.values()) or 1
    for k in scores:
        scores[k] = round(scores[k] / total * 100, 1)
    
    # En yüksek skor
    best = max(scores, key=scores.get)
    
    return {
        "lead": lead_name,
        "category": lead_category,
        "scores": scores,
        "verdict": best,
        "confidence": scores[best]
    }

def score_lead_v2(lead, icp_rules=None):
    """
    v2: Daha detaylı skorlama.
    icp_rules: {'sektorler': ['dis','eczane'], 'sehirler': ['Mudanya','Bursa'], 'min_rating': 4.0}
    """
    score = 50  # Base score
    reasons = []
    
    if icp_rules:
        # Sektör eşleşmesi (+20)
        if lead.get('category') in icp_rules.get('sektorler', []):
            score += 20
            reasons.append("sektör eşleşti")
        else:
            score -= 10
            reasons.append("sektör eşleşmedi")
        
        # Şehir eşleşmesi (+15)
        if lead.get('city') in icp_rules.get('sehirler', []):
            score += 15
            reasons.append("şehir eşleşti")
        
        # Rating (+10)
        rating = lead.get('rating', 0)
        min_r = icp_rules.get('min_rating', 0)
        if rating >= min_r and min_r > 0:
            score += 10
            reasons.append("rating yüksek")
        
        # Website varsa (+10)
        if lead.get('website'):
            score += 10
            reasons.append("websitesi var")
        else:
            score -= 5
            reasons.append("websitesi yok")
    
    score = max(0, min(100, score))
    
    verdict = "hot" if score >= 70 else "warm" if score >= 40 else "cold"
    
    return {
        "lead": lead.get('name', '?'),
        "score": score,
        "verdict": verdict,
        "reasons": reasons
    }

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "demo"
    
    if mode == "demo":
        leads = [
            {"name": "Devadent", "category": "dis", "city": "Mudanya", "rating": 4.8, "website": "devadent.com"},
            {"name": "KRÜEZİ Klinik", "category": "dis", "city": "Mudanya", "rating": 4.5, "website": "kruezi.com"},
            {"name": "Yalı Dent", "category": "dis", "city": "Mudanya", "rating": 4.2, "website": ""},
            {"name": "Özel Çağrı", "category": "hastane", "city": "Bursa", "rating": 3.5, "website": ""},
            {"name": "Mesam Bursa", "category": "dis", "city": "Bursa", "rating": 4.0, "website": "mesam.com"},
        ]
        icp = {"sektorler": ["dis", "eczane"], "sehirler": ["Mudanya", "Bursa"], "min_rating": 4.0}
        
        print(f"{'Lead':15} | {'Skor':5} | {'Karar':6} | {'Sebep'}")
        print("-"*60)
        for l in leads:
            r = score_lead_v2(l, icp)
            print(f"{r['lead']:15} | {r['score']:3}  | {r['verdict']:6} | {', '.join(r['reasons'])}")
