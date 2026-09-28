#!/usr/bin/env python3
"""
Görsel Üretim — Pollinations.ai (ücretsiz)
FAL AI alternatifi. Görsel başına $0.
"""
import os, sys, json, requests, urllib.parse

API_URL = "https://image.pollinations.ai/prompt/{prompt}"

def generate(prompt, width=1080, height=1350, seed=None):
    """Görsel üret, dosyaya kaydet"""
    params = {
        "width": width,
        "height": height,
        "nologo": "true",
    }
    if seed:
        params["seed"] = seed
    
    encoded = urllib.parse.quote(prompt)
    url = f"{API_URL.format(prompt=encoded)}?{'&'.join(f'{k}={v}' for k,v in params.items())}"
    
    r = requests.get(url, timeout=60)
    if r.status_code == 200:
        fname = f"/tmp/hf_img_{hash(prompt)%100000}.jpg"
        with open(fname, "wb") as f:
            f.write(r.content)
        return {"ok": True, "path": fname, "size": len(r.content)}
    else:
        return {"ok": False, "error": f"HTTP {r.status_code}"}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python3 hf-gorsel.py 'prompt'")
        sys.exit(1)
    
    prompt = sys.argv[1]
    result = generate(prompt)
    print(json.dumps(result, indent=2))
