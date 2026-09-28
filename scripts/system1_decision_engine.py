#!/usr/bin/env python3
"""
CyberGene System-1 Fast Decision Engine v1.0 (Jev Architecture)
================================================================
Inspired by TypeSafe AI's Jev Model (System-1 Thinking).
High-speed, typed, zero-generative-text semantic decision layer.

Primitives:
1. choice(state, question, options) -> returns selected option + confidence
2. score(state, rubric) -> returns numerical score (0-10) + confidence
3. boolean(state, statement) -> returns True/False + confidence
"""

import os
import sys
import json
import time
import urllib.request

TYPESAFE_API_KEY = os.environ.get("TYPESAFE_API_KEY")

class System1DecisionEngine:
    def __init__(self, proxy_url="http://127.0.0.1:8999/v1"):
        self.proxy_url = proxy_url
        # Fast model for fallback System-1 decisions: Haiku or Flash-low
        self.fast_model = "claude-3-5-haiku-latest"

    def choice(self, state: dict, question: str, options: list) -> dict:
        """
        Choice Primitive: Pick exactly ONE option from a typed list.
        Returns: {"choice": str, "confidence": float}
        """
        t0 = time.time()
        
        # If TypeSafe API key is configured, use official SDK/API
        if TYPESAFE_API_KEY:
            try:
                from typesafe_sdk import TypeSafeClient
                client = TypeSafeClient(api_key=TYPESAFE_API_KEY)
                res = client.jev.choice(state=state, question=question, options=options)
                return {
                    "choice": res.choice,
                    "confidence": getattr(res, 'confidence', 0.95),
                    "latency_ms": round((time.time() - t0) * 1000, 1),
                    "provider": "typesafe-jev"
                }
            except Exception as e:
                print(f"[System-1] TypeSafe API Exception, falling back: {e}")

        # Local Ultra-Fast System-1 Decision Fallback via Antigravity Proxy
        prompt = f"""
SYSTEM 1 DECISION ENGINE (ZERO GENERATIVE TEXT)
State Context: {json.dumps(state, ensure_ascii=False)}
Question: {question}
Allowed Options: {json.dumps(options, ensure_ascii=False)}

Instruction: Output ONLY valid JSON matching this schema:
{{"choice": "<one of the allowed options>", "confidence": <float between 0.0 and 1.0>}}
Do NOT output any markdown, explanations, or prose.
"""
        payload = json.dumps({
            "model": self.fast_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 50,
            "temperature": 0.0
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.proxy_url}/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw_out = json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"].strip()
                # Clean JSON if any backticks
                if "```json" in raw_out:
                    raw_out = raw_out.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_out:
                    raw_out = raw_out.split("```")[1].split("```")[0].strip()
                
                parsed = json.loads(raw_out)
                parsed["latency_ms"] = round((time.time() - t0) * 1000, 1)
                parsed["provider"] = f"proxy-fast-system1 ({self.fast_model})"
                return parsed
        except Exception as e:
            return {
                "choice": options[0] if options else None,
                "confidence": 0.0,
                "error": str(e),
                "latency_ms": round((time.time() - t0) * 1000, 1)
            }

    def boolean(self, state: dict, statement: str) -> dict:
        """
        Boolean Primitive: Evaluates if a statement is True or False.
        Returns: {"result": bool, "confidence": float}
        """
        res = self.choice(state, f"Is this statement TRUE or FALSE? '{statement}'", ["TRUE", "FALSE"])
        return {
            "result": res.get("choice") == "TRUE",
            "confidence": res.get("confidence", 0.9),
            "latency_ms": res.get("latency_ms", 0),
            "provider": res.get("provider")
        }

    def score(self, state: dict, rubric: str) -> dict:
        """
        Score Primitive: Evaluates a rubric and returns a score 1-10.
        Returns: {"score": int, "confidence": float}
        """
        options = [str(i) for i in range(1, 11)]
        res = self.choice(state, f"Rate from 1 to 10 according to this rubric: '{rubric}'", options)
        try:
            val = int(res.get("choice", "5"))
        except ValueError:
            val = 5
        return {
            "score": val,
            "confidence": res.get("confidence", 0.9),
            "latency_ms": res.get("latency_ms", 0),
            "provider": res.get("provider")
        }


if __name__ == "__main__":
    engine = System1DecisionEngine()

    print("=== CYBERGENE SYSTEM-1 (JEV ARCHITECTURE) TEST ===")

    # Test 1: Lead Routing Decision
    lead_state = {
        "client": "Vetorka Veteriner",
        "domain_status": "DNS_FAILED",
        "issue": "Website is completely dead",
        "google_rating": 4.9,
        "review_count": 640
    }
    decision = engine.choice(
        state=lead_state,
        question="What is the recommended sales action for this lead?",
        options=["SEND_IMMEDIATE_WHATSAPP", "SEND_EMAIL_OFFER", "IGNORE_LEAD", "CALL_PHONE"]
    )
    print("\n[1. LEAD ROUTING DECISION]")
    print(json.dumps(decision, ensure_ascii=False, indent=2))

    # Test 2: Boolean Safety Gate
    message_state = {
        "recipient": "Martur Fompak",
        "proposed_text": "Martur referansımız ile tesisinizin duruş riskini sıfırlıyoruz."
    }
    bool_dec = engine.boolean(
        state=message_state,
        statement="Is this proposed text safe to send without risking brand credibility?"
    )
    print("\n[2. BOOLEAN SAFETY GATE]")
    print(json.dumps(bool_dec, ensure_ascii=False, indent=2))
