#!/usr/bin/env python3
"""
P1 — Semantic Lead Search
Lead'leri anlam bazında ara. "Mudanya'da AI kullanan diş kliniği" gibi.
"""
import os, sys, json, numpy as np
from transformers import AutoTokenizer, AutoModel
import torch

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
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def semantic_search(leads, query, top_k=10):
    """Lead listesinde semantic ara"""
    query_vec = embed(query)
    results = []
    for lead in leads:
        # Lead metnini oluştur
        lead_text = f"{lead.get('name','')} {lead.get('city','')} {lead.get('category','')} {lead.get('notes','')} {lead.get('website','')}"
        lead_vec = embed(lead_text[:500])
        score = cosine_similarity(query_vec, lead_vec)
        results.append((score, lead))
    results.sort(key=lambda x: x[0], reverse=True)
    return [{"score": round(float(s), 3), "lead": l} for s, l in results[:top_k]]

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "search"
    
    if mode == "embed":
        text = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read().strip()
        vec = embed(text).tolist()
        print(json.dumps({"vector": vec, "dim": len(vec), "text": text[:100]}))
    
    elif mode == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else "lead ara"
        # Örnek lead'ler (gerçek veri yoksa demo)
        demo_leads = [
            {"name": "Devadent Ağız ve Diş", "city": "Mudanya", "category": "dis", "notes": "Dijital diş kliniği"},
            {"name": "Özel KRÜEZİ Klinik", "city": "Mudanya", "category": "dis", "notes": "İmplant, estetik diş"},
            {"name": "Yalı Dent", "city": "Mudanya", "category": "dis", "notes": "Genel diş hekimliği"},
            {"name": "Mesam Özel Sağlık", "city": "Bursa", "category": "dis", "notes": "Zincir klinik"},
            {"name": "Özel Çağrı Hastanesi", "city": "Bursa", "category": "hastane", "notes": "Genel hastane"},
        ]
        results = semantic_search(demo_leads, query)
        for r in results:
            print(f"  {r['score']:.3f} | {r['lead']['name']} ({r['lead']['city']})")
