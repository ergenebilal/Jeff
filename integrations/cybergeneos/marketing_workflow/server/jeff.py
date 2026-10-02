"""Jeff for the panel: the real Hermes Jeff (same brain, memory and voice as on Telegram) when HERMES_API_URL and
HERMES_API_KEY are set; a Gemini stand-in only when they are not (local development), and the panel says so."""
import json
import os
import time
import urllib.request

from . import llm
from .context_boundary import DATA_RULES, pack_request

VOICE_RULES = (
    "Bu mesaj Bilal'in CybergeneOS panelindeki sesli konuşmadan geliyor ve cevabın sesli okunacak. Her zamanki Jeff'sin, aynı dil ve aynı kurallarla. "
    "Yalnızca şu biçimi uy: en çok 3 kısa cümle (yaklaşık 45 kelime), düz konuşma dili, markdown, liste, emoji ve uzun çizgi yok, adları ve rakamları düz yaz. "
    "Soru panel verisiyle ilgiliyse aşağıdaki gerçek veriye dayan, uydurma. Uzun anlatman gerekiyorsa kısa özetle ve 'ayrıntıyı yazılı göndereyim mi' diye sor. "
    "Bilal işletme taraması ya da haber taraması isterse cybergeneos becerisindeki panel API'siyle görevi aç (AgencyOS kullanma); "
    "görev panelin Radar ekranında adım adım görünür. Görevi açtıktan sonra 'Radar ekranından izleyebilirsiniz' de; açamadıysan bunu açıkça söyle."
)

FALLBACK_SYSTEM = (
    "Sen Jeff'in yedek kişiliğisin (gerçek Jeff'e şu an bağlı değilsin). Sade, günlük Türkçeyle konuş, 'siz' de. En çok 45 kelime. "
    "Markdown, liste, emoji yok. Yalnızca verilen panel verisine dayan, bilmediğini uydurma. Mesaj gönderemez, kayıt değiştiremezsin. "
    "Cevabın başında kendini 'yedek Jeff' diye tanıt."
)

_state = {"n": 0, "boot": int(time.time())}  # every start opens a clean panel conversation
_fallback_history = []


def hermes_url():
    return os.environ.get("HERMES_API_URL", "").rstrip("/")


def mode():
    """hermes (the real Jeff), yedek (Gemini stand-in) or kapali."""
    if hermes_url() and os.environ.get("HERMES_API_KEY"):
        return "hermes"
    return "yedek" if llm.ready() else "kapali"


def session_id():
    return f"cybergeneos-panel-{_state['boot']}-{_state['n']}"


def reset():
    _state["n"] += 1
    _fallback_history.clear()


def sse_deltas(lines):
    """Text pieces from an OpenAI-style server-sent-events stream. Reasoning and tool progress are ignored."""
    for raw in lines:
        line = raw.decode("utf-8", "replace").strip() if isinstance(raw, bytes) else raw.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            return
        try:
            d = json.loads(payload)
        except ValueError:
            continue
        for ch in d.get("choices") or []:
            piece = (ch.get("delta") or {}).get("content")
            if piece:
                yield piece


def stream_hermes(text, context):
    body = {"model": "jeff", "stream": True, "model_options": {"reasoning_effort": "low"},
            "messages": [{"role": "system", "content": VOICE_RULES + DATA_RULES},
                         {"role": "user", "content": pack_request(text, context)}]}
    req = urllib.request.Request(hermes_url() + "/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + os.environ["HERMES_API_KEY"], "Content-Type": "application/json",
                                          "X-Hermes-Session-Id": session_id()})
    with urllib.request.urlopen(req, timeout=90) as r:
        yield from sse_deltas(r)


def stream_fallback(text, context):
    _fallback_history.append({"role": "user", "text": pack_request(text, context)})
    answer = llm.generate(None, system=FALLBACK_SYSTEM + DATA_RULES, history=_fallback_history[-8:], temperature=0.5, max_tokens=220, timeout=20)
    _fallback_history.append({"role": "model", "text": answer})
    yield answer


def stream_reply(text, context):
    """Yields the reply in pieces as Jeff produces it."""
    m = mode()
    if m == "hermes":
        yield from stream_hermes(text, context)
    elif m == "yedek":
        yield from stream_fallback(text, context)
    else:
        raise RuntimeError("anahtar_yok")
