import sys
import json
import urllib.request

def call_llm(prompt, max_tokens=350):
    url = 'http://127.0.0.1:8999/v1/chat/completions'
    payload = json.dumps({
        'model': 'claude-3-5-sonnet-latest',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=12) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        return res['choices'][0]['message']['content']

def run_adversarial_debate(proposal, client_profile):
    """
    Tez-Antitez Münazara Motoru (ADE L2)
    Model A: İddialı / Satış Odaklı CyberGene
    Model B: Şüpheci / Zor Fabrika Müdürü veya Müşteri
    """
    print(f"=== ADE DEBATE ENGINE BAŞLATILDI ===")
    print(f"Teklif/Mesaj: {proposal}")
    print(f"Müşteri Profili: {client_profile}\n")

    # 1. Antitez (Şüpheci Müşteri İtirazları)
    prompt_anthesis = f"""
    Sen şüpheci, bütçesine hassas, teknolojiden anlamayan ama işinin aksamasına tahammülü olmayan sert bir Fabrika/Klinik Müdürüsün.
    Aşağıdaki teklifi okuyup en acımasız 3 itirazını söyle:
    Teklif: "{proposal}"
    Müşteri Profili: "{client_profile}"
    """
    
    anthesis_out = call_llm(prompt_anthesis, 300)
    print("--- 🔴 MÜŞTERİ İTİRAZLARI (ANTİTEZ) ---")
    print(anthesis_out)

    # 2. Sentez & Kurşun Geçirmez Teklif
    prompt_synthesis = f"""
    Müşterinin itirazları şunlar oldu:
    {anthesis_out}
    
    Bu itirazları %100 nötralize eden, güven veren ve müşteriyi ikna eden revize edilmiş kurşun geçirmez teklif metnini yaz.
    """

    synthesis_out = call_llm(prompt_synthesis, 400)
    print("\n--- 🟢 REVİZE EDİLMİŞ KURŞUN GEÇİRMEZ TEKLİF (SENTEZ) ---")
    print(synthesis_out)

if __name__ == "__main__":
    run_adversarial_debate(
        proposal="Martur referanslı çelik konstrüksiyon ve bakım desteğimizle fabrikanızın duruş riskini sıfırlıyoruz.",
        client_profile="NOSAB Otomotiv Yan Sanayi Fabrika Müdürü"
    )
