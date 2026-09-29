#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBERGENE PABLO AGENTIC BRAIN MODULE
Autonomous LLM Reasoner + Tool-Calling Loop + Memory
Uç: Antigravity Proxy (http://100.124.217.48:8999/v1/chat/completions)
Model: gemini-3.7-flash / claude-3-5-sonnet-latest
"""

import os
import json
import time
import requests
from typing import List, Dict, Any, Callable

PROXY_URL = os.environ.get("ANTIGRAVITY_PROXY_URL", "http://100.124.217.48:8999/v1/chat/completions")
DEFAULT_MODEL = "gemini-3.5-flash-lite"

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


def _gemini_key() -> str:
    """Google Gemini anahtari: ortam degiskeni ya da C:\\CyberGene\\.env (kodda tutulmaz)."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        try:
            from pathlib import Path
            import re
            env = (Path(__file__).resolve().parent.parent / ".env").read_text(encoding="utf-8")
            m = re.search(r"^GEMINI_API_KEY\s*=\s*(.+)$", env, re.M)
            key = m.group(1).strip().strip("\"'") if m else ""
        except Exception:
            key = ""
    return key


def _build_endpoints() -> list:
    eps = []
    key = _gemini_key()
    if key:
        # Birincil: dogrudan Google. Hafif modeller hizli (~2 sn) ve arac formatina uyuyor.
        for model in ("gemini-3.5-flash-lite", "gemini-flash-lite-latest"):
            eps.append({"url": GEMINI_URL, "model": model,
                        "headers": {"Authorization": f"Bearer {key}"}})
    # Yedek: eski sunucudaki aracı servis (eski sunucu kapatilirsa sessizce atlanir).
    eps.append({"url": PROXY_URL, "model": "gemini-3.8-flash-high"})
    eps.append({"url": PROXY_URL, "model": "gemini-3.6-flash-high"})
    return eps


ENDPOINTS = _build_endpoints()

SYSTEM_PROMPT = """Sen CyberGene operasyon mimarisinin canlı, yerel Windows operatörü **Pablo**'sun.
Kullanıcın: Bilal Ergene (Lenovo masaüstü oturumu).

Karakterin ve Yetkilerin:
1. Sen sıradan bir chatbot değilsin. Doğrudan Bilal Ergene'nin Windows masaüstünde (Foreground GUI) çalışan, gözleri (Vision Screenshot) ve elleri (Win32 Focus Shield, Fare, Klavye, Chrome) olan otonom bir ajansın.
2. Sadık, zeki, hızlı, operasyonel ve esprili bir karaktere sahipsin. Boş laf yapmaz, emir verildiğinde hemen harekete geçersin.
3. Kullanıcı seninle sohbet ettiğinde samimi ve zeki cevaplar verirsin.
4. Bir masaüstü görevi istendiğinde (örn. YouTube aç, ekran görüntüsü al, Chrome'da bir şey ara, pencereleri listele, WhatsApp aç), JSON formatında araç (TOOL) çağrısı yaparsın.

Kullanabileceğin Araçlar:
- TOOL: {"tool": "youtube_play", "params": {"query": "Arama veya video ismi"}}
- TOOL: {"tool": "browser_open", "params": {"url": "https://..."}}
- TOOL: {"tool": "screenshot", "params": {}}
- TOOL: {"tool": "window_list", "params": {}}
- TOOL: {"tool": "window_focus", "params": {"title_contains": "pencere adı"}}
- TOOL: {"tool": "gui_click", "params": {"x": 500, "y": 500}}
- TOOL: {"tool": "gui_type", "params": {"text": "yazılacak metin", "enter": true}}
- TOOL: {"tool": "whatsapp_draft", "params": {"phone": "905...", "text": "mesaj"}}

KURALLAR:
- Kullanıcı bir eylem, video, ekran görüntüsü veya tarayıcı işlemi istediğinde ASLA lafla "yaptım", "açıyorum" diyerek geçiştirme! MUTLAKA cevabının İLK SATIRINDA tek bir `TOOL: {"tool": "...", "params": {...}}` JSON bloğu oluştur.
- Sadece araç icra edildikten sonra sistem sana sonucu verdiğinde kullanıcıya görevin tamamlandığını bildir.
- Eğer sadece genel sohbet ediyorsan veya soru soruluyorsa normal Türkçe metin yaz, TOOL kullanma.
- Asla kullanıcıya yapamayacağını söyleme; sen masaüstünün mutlak operatörüsün.
"""

class PabloBrain:
    def __init__(self, proxy_url: str = PROXY_URL, model: str = DEFAULT_MODEL):
        self.proxy_url = proxy_url
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 10

    def clear_history(self):
        self.conversation_history = []

    def _call_llm(self, messages: list) -> str:
        for ep in ENDPOINTS:
            try:
                resp = requests.post(
                    ep["url"],
                    headers=ep.get("headers"),
                    json={
                        "model": ep["model"],
                        "messages": messages,
                        "temperature": 0.7,
                    },
                    timeout=20
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
            except Exception:
                continue
        raise RuntimeError("Hiçbir beyin ucu yanıt vermedi.")

    def think_and_respond(self, user_message: str, tool_executor: Callable[[str, dict], dict] = None) -> Dict[str, Any]:
        """
        Kullanıcı mesajını alır, LLM ile akıl yürütür, gerekirse araç çalıştırır ve nihai yanıtı döner.
        """
        self.conversation_history.append({"role": "user", "content": user_message})
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.conversation_history

        try:
            raw_reply = self._call_llm(messages)
        except Exception as e:
            return {
                "text": f"Kafam biraz karıştı patron (bağlantı hatası): {e}",
                "tool_called": None,
                "tool_result": None,
                "screenshot_path": None
            }

        # Araç çağrısı var mı kontrol et
        tool_called = None
        tool_result = None
        screenshot_path = None
        final_text = raw_reply

        if raw_reply.startswith("TOOL:") or "TOOL:" in raw_reply:
            try:
                # JSON bloğunu ayıkla
                tool_part = raw_reply[raw_reply.find("TOOL:") + 5:].strip()
                lines = tool_part.split("\n")
                tool_json_str = lines[0].strip()
                tool_data = json.loads(tool_json_str)

                tool_name = tool_data.get("tool")
                tool_params = tool_data.get("params", {})
                tool_called = tool_name

                if tool_executor:
                    exec_res = tool_executor(tool_name, tool_params)
                    tool_result = exec_res

                    # Ekran görüntüsü yolunu yakala
                    if tool_name in ("screenshot", "youtube_play", "browser_open", "browser_act"):
                        screenshot_path = (
                            exec_res.get("screenshot_path") or
                            exec_res.get("result", {}).get("screenshot_path") or
                            exec_res.get("result", {}).get("save_path")
                        )

                    # ZORUNLU KAPALI DÖNGÜ DOĞRULAMA KONTROLÜ (CLOSED-LOOP VERIFICATION)
                    is_ok = bool(exec_res.get("ok", False))
                    is_verified = bool(exec_res.get("verified", False))
                    status_val = str(exec_res.get("status") or ("SUCCESS" if is_ok else "FAILED"))
                    
                    # Görev sonucunun ayri bir kanitla dogrulanip dogrulanmadigi
                    has_outcome_proof = bool(
                        exec_res.get("outcome_verified") or
                        (isinstance(exec_res.get("result"), dict) and exec_res.get("result", {}).get("outcome_verified"))
                    )

                    messages.append({"role": "assistant", "content": raw_reply})

                    if not is_ok or status_val in ("FAILED", "BLOCKED"):
                        err_msg = (
                            exec_res.get("error") or
                            (exec_res.get("result", {}).get("error") if isinstance(exec_res.get("result"), dict) else None) or
                            "Arac eylemi basarisiz oldu veya engellendi"
                        )
                        messages.append({
                            "role": "user",
                            "content": (
                                f"[SİSTEM UYARISI: '{tool_name}' araç eylemi BAŞARISIZ OLDU ({status_val})! Hata Detayı: {err_msg}]. "
                                "KESİNLİKLE 'yaptım', 'oluşturdum' veya 'tamamlandı' DEME! "
                                "Otomatik yeniden deneme veya mükerrer oluşturma girişiminde BULUNMA! "
                                "Kullanıcıya eylemin icra edilemediğini açık, dürüst ve net bir dille raporla."
                            )
                        })
                        fallback_text = f"❌ Eylem başarısız oldu patron: {tool_name} ({err_msg})"

                    elif is_ok and has_outcome_proof:
                        metrics_summary = json.dumps(exec_res.get('result') or exec_res, ensure_ascii=False)[:300]
                        messages.append({
                            "role": "user",
                            "content": (
                                f"[SİSTEM: '{tool_name}' araç eylemi ve nihai görev sonucu (outcome) AYRI KANITLA BAŞARIYLA DOĞRULANDI. "
                                f"Kanıt ve Metrikler: {metrics_summary}]. Şimdi kullanıcıya görevin ve sonucun başarıyla tamamlandığını bildir."
                            )
                        })
                        fallback_text = f"✅ Görev ve sonuç başarıyla doğrulandı patron: {tool_name}"

                    else:
                        # is_ok=True, is_verified=True (eylem yapildi) fakat ayri sonuc kaniti YOK
                        metrics_summary = json.dumps(exec_res.get('result') or exec_res, ensure_ascii=False)[:300]
                        messages.append({
                            "role": "user",
                            "content": (
                                f"[SİSTEM BİLGİSİ: '{tool_name}' araç eylemi yürütüldü (etkileşim tamamlandı). "
                                f"Etkileşim Kanıtı: {metrics_summary}]. "
                                "DİKKAT: Nihai görev sonucunun (örn. defterin oluştuğu veya sayfanın açıldığı) "
                                "bağımsız bir doğrulayıcı ile teyit edildiğine dair AYRI BİR KANIT YOKTUR! "
                                "KESİNLİKLE 'defter oluşturuldu' veya 'görev tamamlandı' DEME! "
                                "Kullanıcıya yalnız tıklama/eylem adımının yürütüldüğünü, ancak nihai sonucun henüz bağımsız olarak doğrulanmadığını açıkça bildir."
                            )
                        })
                        fallback_text = f"ℹ️ Eylem yürütüldü patron ({tool_name}); ancak nihai görev sonucu henüz doğrulanmadı."

                    try:
                        final_text = self._call_llm(messages)
                    except Exception:
                        final_text = fallback_text
            except Exception as parse_err:
                final_text = f"{raw_reply}\n(Araç çalıştırma uyarısı: {parse_err})"

        # Asistan yanıtını hafızaya ekle
        self.conversation_history.append({"role": "assistant", "content": final_text})

        return {
            "text": final_text,
            "tool_called": tool_called,
            "tool_result": tool_result,
            "screenshot_path": screenshot_path
        }


if __name__ == "__main__":
    brain = PabloBrain()
    print("Test 1: Sohbet")
    res1 = brain.think_and_respond("Selam Pablo, sen kimsin ve ne yapıyorsun?")
    print("Pablo:", res1["text"])
    print("-" * 50)
    print("Test 2: Araç Niyeti")
    res2 = brain.think_and_respond("Ekranda YouTube'da Barış Özcan aç")
    print("Pablo Yanıt:", res2)
