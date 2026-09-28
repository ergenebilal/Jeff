import os
import sys
import json
import urllib.request
import base64

def run_vision_quality_gate(image_path):
    if not os.path.exists(image_path):
        print(f"Hata: Görsel bulunamadı -> {image_path}")
        return False

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Call proxy with image input in OpenAI/Antigravity payload format
    url = "http://127.0.0.1:8999/v1/chat/completions"
    payload = json.dumps({
        "model": "claude-3-5-sonnet-latest",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "Ekteki görseli detaylıca oku ve görselin içinde yazan başlıkları, renkleri ve stili analiz ederek CyberGene editoryal standartlarına göre puanla (X/10) ve [APPROVED] veya [REJECTED] yaz."
                    }
                ]
            }
        ],
        "max_tokens": 300
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            content = res["choices"][0]["message"]["content"]
            print("=== VISION KALİTE KAPISI DEĞERLENDİRMESİ ===")
            print(content)
            return "APPROVED" in content
    except Exception as e:
        print(f"Vision Kapısı Hatası: {e}")
        return False

if __name__ == "__main__":
    test_img = "/home/hermes/pipeline/output/v8-dis-s-1.png"
    run_vision_quality_gate(test_img)
