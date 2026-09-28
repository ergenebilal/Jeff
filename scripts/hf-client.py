#!/usr/bin/env python3
"""
HF Client — Merkezi Hugging Face Inference API aracı
Tüm HF modellerini tek bir interface'den çağırır.
"""
import os
import sys
import json
import requests
import argparse
from typing import Optional

HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    # .env'den oku
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("HF_TOKEN="):
                    HF_TOKEN = line.split("=", 1)[1].strip()
                    break

API_URL = "https://api-inference.huggingface.co/models/{model_id}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}


def call_model(model_id: str, payload: dict, timeout: int = 60) -> dict:
    """Herhangi bir HF modelini çağır."""
    url = API_URL.format(model_id=model_id)
    r = requests.post(url, headers=HEADERS, json=payload, timeout=timeout)
    
    if r.status_code == 503:
        # Model yükleniyor — bekle ve tekrar dene
        import time
        print(f"  ⏳ Model {model_id} yükleniyor, 20sn bekliyorum...", file=sys.stderr)
        time.sleep(20)
        r = requests.post(url, headers=HEADERS, json=payload, timeout=timeout)
    
    if r.status_code != 200:
        return {"error": True, "status": r.status_code, "text": r.text[:500]}
    
    try:
        return r.json()
    except:
        return {"error": True, "raw": r.content[:500]}


def embed(text: str, model: str = "sentence-transformers/all-MiniLM-L6-v2") -> list:
    """Metin → embedding vektörü (384 boyut)"""
    result = call_model(model, {"inputs": text})
    if isinstance(result, list) and len(result) > 0:
        return result[0] if isinstance(result[0], list) else result
    return []


def classify(text: str, labels: list, model: str = "facebook/bart-large-mnli") -> dict:
    """Zero-shot classification: metni etiketlere göre sınıflandır"""
    result = call_model(model, {
        "inputs": text,
        "parameters": {"candidate_labels": labels}
    })
    if isinstance(result, dict) and "labels" in result:
        return {
            "text": text[:100],
            "labels": result["labels"],
            "scores": result["scores"],
            "top_label": result["labels"][0],
            "top_score": result["scores"][0]
        }
    return {"error": str(result)}


def generate_image(prompt: str, model: str = "black-forest-labs/FLUX.1-dev") -> Optional[bytes]:
    """Metin → görsel (HF Inference API üzerinden)"""
    result = call_model(model, {"inputs": prompt}, timeout=120)
    if isinstance(result, bytes) or (isinstance(result, dict) and "raw" in result):
        return result if isinstance(result, bytes) else result.get("raw")
    if isinstance(result, list) and len(result) > 0:
        # Bazı modeller base64 döner
        import base64
        if isinstance(result[0], dict) and "image" in result[0]:
            return base64.b64decode(result[0]["image"])
    return None


def tts(text: str, model: str = "hexgrad/Kokoro-82M") -> Optional[bytes]:
    """Metin → ses"""
    result = call_model(model, {"inputs": text}, timeout=60)
    if isinstance(result, bytes):
        return result
    if isinstance(result, dict) and "raw" in result:
        return result.get("raw")
    return None


def translate(text: str, source: str = "eng_Latn", target: str = "tur_Latn",
              model: str = "facebook/nllb-200-distilled-600M") -> str:
    """Çeviri"""
    result = call_model(model, {
        "inputs": text,
        "parameters": {"src_lang": source, "tgt_lang": target}
    })
    if isinstance(result, list) and len(result) > 0:
        return result[0].get("translation_text", str(result[0]))
    return str(result)


def main():
    parser = argparse.ArgumentParser(description="HF Client — Hugging Face Inference API")
    parser.add_argument("mode", choices=["embed", "classify", "image", "tts", "translate", "test"],
                        help="İşlem türü")
    parser.add_argument("input", nargs="?", help="Metin/prompt")
    parser.add_argument("--model", default=None, help="Model ID (override)")
    parser.add_argument("--labels", default=None, help="Sınıflandırma etiketleri (virgüllü)")
    parser.add_argument("--source", default="eng_Latn", help="Kaynak dil")
    parser.add_argument("--target", default="tur_Latn", help="Hedef dil")
    
    args = parser.parse_args()
    
    if args.mode == "test":
        print("🔌 HF Client Test")
        print(f"  Token: {'✅ Var' if HF_TOKEN else '❌ Yok'}")
        print(f"  Test: ping HF API...")
        r = requests.get("https://huggingface.co/api/models?limit=1")
        print(f"  API: {'✅ Canlı' if r.status_code == 200 else '❌ Sorunlu'} ({r.status_code})")
        return
    
    if not args.input:
        print("❌ Metin gerekli", file=sys.stderr)
        sys.exit(1)
    
    if args.mode == "embed":
        model = args.model or "sentence-transformers/all-MiniLM-L6-v2"
        result = embed(args.input, model)
        print(json.dumps({"vector_length": len(result), "first_5": result[:5]}))
    
    elif args.mode == "classify":
        if not args.labels:
            print("❌ --labels gerekli (örn: 'hot,warm,cold')", file=sys.stderr)
            sys.exit(1)
        model = args.model or "facebook/bart-large-mnli"
        labels = [l.strip() for l in args.labels.split(",")]
        result = classify(args.input, labels, model)
        print(json.dumps(result, indent=2))
    
    elif args.mode == "image":
        model = args.model or "black-forest-labs/FLUX.1-dev"
        img = generate_image(args.input, model)
        if img:
            path = f"/tmp/hf_image_{hash(args.input) % 100000}.png"
            with open(path, "wb") as f:
                f.write(img if isinstance(img, bytes) else img)
            print(json.dumps({"ok": True, "path": path, "size": len(img)}))
        else:
            print(json.dumps({"ok": False, "error": "Görsel üretilemedi"}))
    
    elif args.mode == "tts":
        model = args.model or "hexgrad/Kokoro-82M"
        audio = tts(args.input, model)
        if audio:
            path = f"/tmp/hf_tts_{hash(args.input) % 100000}.wav"
            with open(path, "wb") as f:
                f.write(audio if isinstance(audio, bytes) else audio)
            print(json.dumps({"ok": True, "path": path, "size": len(audio)}))
        else:
            print(json.dumps({"ok": False, "error": "Ses üretilemedi"}))
    
    elif args.mode == "translate":
        result = translate(args.input, args.source, args.target, 
                          args.model or "facebook/nllb-200-distilled-600M")
        print(json.dumps({"ok": True, "translation": result}))


if __name__ == "__main__":
    main()
