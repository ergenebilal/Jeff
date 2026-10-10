#!/usr/bin/env python3
# -*- coding: utf-8 -*-
('\nANTIGRAVITY 24/7 HYBRID TELEGRAM CONTROLLER & AUTONOMOUS SURGEON\n-----------------------------------------------------------------\nHost: Jeff Linux Server (100.124.217.48 - Always Online 24/7)\nRemote Node: Lenovo Windows Laptop (100.89.26.86:7788 - Pablo)\nBot: configured via TELEGRAM_BOT_TOKEN\nOwner & Operator: Bilal Ergene (chat_id: ' + __import__('os').environ.get('TELEGRAM_OWNER_CHAT_ID', '') + ')\n')

import os
import sys
import time
import json
import psutil
import shutil
import re
import ast
import base64
import urllib.request
import urllib.parse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
AUTHORIZED_CHATS = [int(__import__('os').environ.get('TELEGRAM_OWNER_CHAT_ID', '0'))]  # Bilal Ergene

WINDOWS_TAILSCALE_IP = "100.89.26.86"
WINDOWS_NODE_PORT = 7788
WINDOWS_NODE_URL = f"http://{WINDOWS_TAILSCALE_IP}:{WINDOWS_NODE_PORT}"
BRIDGE_KEY = os.environ.get("BRIDGE_KEY")

# LLM Proxy is on Jeff localhost port 8999
LLM_PROXY_URL = "http://127.0.0.1:8999/v1/chat/completions"

BASE_DIR = Path("/opt/hermes")
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
BOT_LOG_FILE = LOGS_DIR / "antigravity_telegram_bot.log"
TEMP_DIR = Path("/tmp/antigravity_bot")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(BOT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ── TELEGRAM API ENGINE ───────────────────────────────────────────────────────
def tg_request(method: str, payload: dict = None, timeout: int = 30) -> dict:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json"} if payload else {}
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log(f"[TG ERROR] {method}: {e}")
        return {"ok": False, "error": str(e)}


def send_msg(chat_id: int, text: str, reply_markup: dict = None) -> bool:
    """Sends message with automatic splitting for long texts to avoid Telegram 4096 char limits."""
    MAX_CHUNK = 3800
    if len(text) <= MAX_CHUNK:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        res = tg_request("sendMessage", payload)
        if not res.get("ok"):
            payload.pop("parse_mode", None)
            res = tg_request("sendMessage", payload)
        return res.get("ok", False)

    chunks = []
    lines = text.split("\n")
    curr = ""
    for line in lines:
        if len(curr) + len(line) + 1 > MAX_CHUNK:
            chunks.append(curr)
            curr = line + "\n"
        else:
            curr += line + "\n"
    if curr.strip():
        chunks.append(curr)

    success = True
    for i, chunk in enumerate(chunks):
        markup = reply_markup if i == len(chunks) - 1 else None
        p = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        if markup:
            p["reply_markup"] = markup
        r = tg_request("sendMessage", p)
        if not r.get("ok"):
            p.pop("parse_mode", None)
            r = tg_request("sendMessage", p)
        if not r.get("ok"):
            success = False
        time.sleep(0.3)
    return success


def send_photo(chat_id: int, photo_path: Path, caption: str = "") -> bool:
    if not photo_path.exists():
        send_msg(chat_id, f"⚠️ Fotoğraf bulunamadı: {photo_path}")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    boundary = f"----WebKitFormBoundary{int(time.time()*1000)}"

    body = bytearray()
    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n".encode("utf-8"))
    if caption:
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode("utf-8"))
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"parse_mode\"\r\n\r\nHTML\r\n".encode("utf-8"))

    filename = photo_path.name
    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{filename}\"\r\nContent-Type: image/png\r\n\r\n".encode("utf-8"))
    with open(photo_path, "rb") as f:
        body.extend(f.read())
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("ok", False)
    except Exception as e:
        log(f"[TG PHOTO ERROR] {e}")
        return False


def answer_callback(cb_id: str, text: str = None):
    payload = {"callback_query_id": cb_id}
    if text:
        payload["text"] = text
    tg_request("answerCallbackQuery", payload)


# ── NODE STATUS & DISCOVERY ───────────────────────────────────────────────────
def check_windows_status() -> dict:
    """Checks if Lenovo Windows laptop (Pablo) is online over Tailscale."""
    try:
        req = urllib.request.Request(f"{WINDOWS_NODE_URL}/health")
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                return {"online": True, "node": data.get("node", "Pablo"), "version": data.get("version", "2.1.0"), "mode": data.get("mode", "ONLINE")}
    except Exception:
        pass
    return {"online": False}


def get_system_status() -> str:
    # 1. Jeff Linux Stats
    cpu = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    uptime_s = time.time() - psutil.boot_time()
    uptime_d = int(uptime_s // 86400)
    uptime_h = int((uptime_s % 86400) // 3600)

    # 2. Windows Node Stats
    win_stat = check_windows_status()
    if win_stat["online"]:
        win_text = f"🟢 <b>ÇEVRİMİÇİ</b> (Sürüm: <code>{win_stat.get('version')}</code>)"
        win_details = "• Masaüstü, Chrome ve Windows dosya kontrolleri devrede."
    else:
        win_text = "🔴 <b>KAPALI / UYKUDA</b>"
        win_details = "• Bilgisayar kapalı olduğunda Jeff 7/24 çalışmaya devam eder."

    msg = (
        "🛸 <b>ANTIGRAVITY HİBRİT SİSTEM DURUMU</b>\n"
        "────────────────────────\n"
        "🐧 <b>JEFF (Linux Sunucu - 7/24 Kesintisiz):</b>\n"
        f"• <b>Durum:</b> 🟢 Aktif (Uptime: {uptime_d} gün, {uptime_h} saat)\n"
        f"• <b>İşlemci (CPU):</b> %{cpu}\n"
        f"• <b>Bellek (RAM):</b> %{ram}\n"
        f"• <b>Disk (/):</b> %{disk}\n"
        f"• <b>LLM Proxy:</b> 🟢 :8999 Çevrimiçi\n\n"
        "🪟 <b>LENOVO MASAÜSTÜ (Pablo Node - 100.89.26.86):</b>\n"
        f"• <b>Durum:</b> {win_text}\n"
        f"{win_details}\n"
        "────────────────────────\n"
        f"• <b>Zaman:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    return msg


# ── BRIDGE CALL HELPER (JEFF -> WINDOWS) ──────────────────────────────────────
def call_windows_bridge(action: str, params: dict = None, timeout: int = 25) -> dict:
    """Executes action on Windows node via Tailscale HTTP REST bridge."""
    import sys
    sys.path.insert(0, '/home/hermes/.hermes/scripts')
    import alfred_tool
    return alfred_tool.execute(action, params or {}, timeout=timeout)


# ── DUAL-NODE SURGICAL TOOLS ──────────────────────────────────────────────────

def tool_jeff_shell(cmd: str) -> str:
    """Runs shell command locally on Jeff Linux."""
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        out = p.stdout.strip()
        err = p.stderr.strip()
        res = []
        if out:
            res.append(f"[JEFF STDOUT]\n{out[:3000]}")
        if err:
            res.append(f"[JEFF STDERR]\n{err[:1000]}")
        if not res:
            res.append(f"(Exited with code {p.returncode}, empty output)")
        return "\n".join(res)
    except Exception as e:
        return f"ERROR jeff_shell: {e}"


def tool_jeff_view_file(path: str, start_line: int = 1, end_line: int = 120) -> str:
    try:
        p = Path(path)
        if not p.exists():
            return f"ERROR: File not found on Jeff: {path}"
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        tot = len(lines)
        start = max(1, int(start_line))
        end = min(tot, int(end_line))
        res = [f"--- Jeff: {path} (lines {start}-{end} of {tot}) ---"]
        for i in range(start - 1, end):
            res.append(f"{i + 1:4d}: {lines[i]}")
        return "\n".join(res)
    except Exception as e:
        return f"ERROR jeff_view_file: {e}"


def tool_windows_shell(cmd: str) -> str:
    """Runs shell command on Windows Lenovo PC via bridge."""
    win_stat = check_windows_status()
    if not win_stat["online"]:
        return "ERROR: Lenovo Windows masaüstü şu anda kapalı/çevrimdışı. Bilgisayarınızı açtığınızda çalıştırılabilir."

    res = call_windows_bridge("shell", {"command": cmd})
    if res.get("ok"):
        out = res.get("result", {}).get("stdout", "").strip()
        err = res.get("result", {}).get("stderr", "").strip()
        r = []
        if out:
            r.append(f"[WINDOWS STDOUT]\n{out[:3000]}")
        if err:
            r.append(f"[WINDOWS STDERR]\n{err[:1000]}")
        if not r:
            r.append(f"(Exited with code {res.get('result', {}).get('exit_code', 0)}, empty output)")
        return "\n".join(r)
    return f"ERROR windows_shell: {res.get('error', 'Unknown failure')}"


def tool_windows_view_file(path: str, start_line: int = 1, end_line: int = 100) -> str:
    """Reads file from Windows workspace."""
    ps_cmd = f"Get-Content -Path '{path}' -Encoding UTF8 | Select-Object -Skip {start_line - 1} -First {end_line - start_line + 1}"
    return tool_windows_shell(f'powershell -NoProfile -Command "{ps_cmd}"')


def tool_windows_screenshot(chat_id: int) -> str:
    """Captures screenshot from Windows desktop and sends it to Telegram."""
    win_stat = check_windows_status()
    if not win_stat["online"]:
        return "ERROR: Lenovo Windows masaüstü şu anda kapalı/çevrimdışı. Ekran görüntüsü alınamaz."

    res = call_windows_bridge("screenshot", {})
    if res.get("ok"):
        b64_data = res.get("result", {}).get("screenshot_b64")
        if b64_data:
            local_ss = TEMP_DIR / f"desktop_ss_{int(time.time())}.png"
            with open(local_ss, "wb") as f:
                f.write(base64.b64decode(b64_data))
            send_photo(chat_id, local_ss, "📸 <b>Lenovo Masaüstü Canlı Ekran Görüntüsü</b>")
            return "SUCCESS: Screenshot captured and sent to Telegram chat."
    return f"ERROR windows_screenshot: {res.get('error', 'Screenshot capture failed')}"


def tool_pablo_action(action: str, params: dict = None) -> str:
    """Executes Pablo action on Windows (restart, browser, etc)."""
    win_stat = check_windows_status()
    if not win_stat["online"]:
        return "ERROR: Lenovo Windows masaüstü kapalı/çevrimdışı."

    action = action.lower().strip()
    if action in ("restart", "yeniden"):
        return tool_windows_shell('python "c:/AI AGENTS PROJECT/scratch/sync_and_restart_node.py"')
    res = call_windows_bridge(action, params)
    return json.dumps(res, indent=2, ensure_ascii=False)


def tool_guardian_verify() -> str:
    """Runs Guardian verification on Jeff or Windows."""
    # Guardian on Jeff
    try:
        p = subprocess.run("python3 /home/hermes/guardian_files/guardian.py verify-baseline", shell=True, capture_output=True, text=True, timeout=15)
        if p.returncode == 0:
            return f"[JEFF GUARDIAN]\n{p.stdout.strip()}"
    except Exception:
        pass
    # If not on Jeff, run on Windows
    return tool_windows_shell('python "C:/Users/lenovo/.openclaw/guardian/guardian.py" verify-baseline')


def tool_pilot_action(sub_action: str = "status") -> str:
    """Controls Faz 4 pilot on Windows (status, approve, run, dry_run)."""
    win_stat = check_windows_status()
    if not win_stat["online"]:
        return "ERROR: Lenovo Windows masaüstü kapalı/çevrimdışı. Pilot oturumu başlatılamaz."
    sub = sub_action.lower().strip()
    if sub == "approve":
        return tool_windows_shell('python "c:/AI AGENTS PROJECT/pablo_pilot_runner.py" --approve')
    elif sub in ("run", "baslat", "start"):
        return tool_windows_shell('python "c:/AI AGENTS PROJECT/pablo_pilot_runner.py"')
    elif sub in ("dry_run", "simulasyon"):
        return tool_windows_shell('python "c:/AI AGENTS PROJECT/pablo_pilot_runner.py" --dry-run')
    else:
        return tool_windows_shell('python "c:/AI AGENTS PROJECT/pablo_pilot_runner.py" --status')


# ── TOOL EXTRACTOR & AGENTIC RE-ACT LOOP ──────────────────────────────────────

def extract_tool_call(text: str) -> Optional[dict]:
    blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    for b in blocks:
        try:
            d = json.loads(b)
            if "tool" in d:
                return d
        except Exception:
            continue

    idx = text.find('{"')
    if idx == -1:
        idx = text.find('{ "')
    if idx != -1:
        depth = 0
        start = idx
        for i in range(start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    cand = text[start:i+1]
                    try:
                        d = json.loads(cand)
                        if "tool" in d:
                            return d
                    except Exception:
                        pass
                    break
    return None


def execute_agent_tool(tool_name: str, params: dict, chat_id: int) -> str:
    tool_name = tool_name.lower().strip()
    log(f"[HYBRID TOOL] {tool_name} with params: {params}")

    if tool_name == "jeff_shell":
        return tool_jeff_shell(params.get("cmd", ""))
    elif tool_name == "jeff_view_file":
        return tool_jeff_view_file(params.get("path", ""), params.get("start_line", 1), params.get("end_line", 100))
    elif tool_name == "windows_shell":
        return tool_windows_shell(params.get("cmd", ""))
    elif tool_name == "windows_view_file":
        return tool_windows_view_file(params.get("path", ""), params.get("start_line", 1), params.get("end_line", 80))
    elif tool_name in ("windows_screenshot", "screenshot", "take_screenshot"):
        return tool_windows_screenshot(chat_id)
    elif tool_name == "pablo_action":
        return tool_pablo_action(params.get("action", "ping"), params.get("params"))
    elif tool_name == "guardian_verify":
        return tool_guardian_verify()
    elif tool_name == "pilot_action":
        return tool_pilot_action(params.get("action", "status"))
    else:
        return f"ERROR: Unknown tool '{tool_name}'."


CONVERSATION_HISTORY: Dict[int, List[Dict[str, str]]] = {}

SYSTEM_SURGEON_PROMPT = """Sen Google Deepmind Antigravity sisteminin Telegram üzerinden çalışan 7/24 HİBRİT SİSTEM MİMARI VE KOD CERRAHISIN.
Kullanıcın: Bilal Ergene (Lenovo masaüstü sahibi, sistem mimarı).

Konumun: Jeff Linux Sunucusu (7/24 Kesintisiz Aktif: 100.124.217.48).
Bağlantılı Node: Lenovo Windows Laptop (Pablo: 100.89.26.86:7788 - Tailscale üzerinden bağlı).

Sistem Çift Düğümlüdür (Hibrit):
1. Bilgisayar kapalı olsa dahi sen Jeff üzerinde 7/24 kesintisiz yaşarsın.
2. Bilgisayar açık olduğunda Tailscale üzerinden Windows'a bağlanır, masaüstü ekran görüntülerini çeker, Windows dosyalarını cerrahi olarak düzenler ve Pablo tarayıcısını yönetirsin.
3. Bilgisayar kapalıyken Windows işlemi istenirse kullanıcıya bilgisayarın kapalı olduğunu, Jeff üzerindeki işlemlerin devam ettiğini bildirirsin.

Kullanabileceğin Araçlar:
1. `jeff_shell`: Jeff Linux sunucusunda bash komutu çalıştır.
   {"tool": "jeff_shell", "params": {"cmd": "uptime && ps aux | grep python"}}

2. `jeff_view_file`: Jeff Linux sunucusundaki dosyayı satır satır oku.
   {"tool": "jeff_view_file", "params": {"path": "/opt/hermes/telegram_claude_bot.py", "start_line": 1, "end_line": 60}}

3. `windows_shell`: Lenovo Windows masaüstünde (c:\\AI AGENTS PROJECT) PowerShell/CMD çalıştır.
   {"tool": "windows_shell", "params": {"cmd": "python test_pablo_grounding_suite.py"}}

4. `windows_view_file`: Windows üzerindeki dosyayı oku.
   {"tool": "windows_view_file", "params": {"path": "c:/AI AGENTS PROJECT/hermes_node.py", "start_line": 1, "end_line": 60}}

5. `windows_screenshot`: Windows masaüstünün anlık ekran görüntüsünü alıp Telegram'a fotoğraf ilet.
   {"tool": "windows_screenshot", "params": {}}

6. `pablo_action`: Pablo node kontrolü (action: "restart", "ping", "browser_open", "youtube_play").
   {"tool": "pablo_action", "params": {"action": "restart"}}

7. `guardian_verify`: 28/28 Guardian baseline bütünlüğünü doğrula.
   {"tool": "guardian_verify", "params": {}}

8. `pilot_action`: Faz 4 LinkedIn pilot kontrolü (action: "status", "approve", "run", "dry_run").
   {"tool": "pilot_action", "params": {"action": "status"}}

KURALLAR:
- Araç çağırmak istediğinde SADECE yukarıdaki JSON formatında yanıt ver (markdown ```json ... ``` içinde veya saf JSON).
- Başka araç çağırmaya gerek kalmadığında veya işlem tamamlandığında, Bilal Bey'e Türkçe, net, profesyonel ve teknik bir ameliyat/durum raporu sun.
"""


def call_antigravity_brain(user_text: str, chat_id: int) -> str:
    history = CONVERSATION_HISTORY.get(chat_id, [])
    messages = [{"role": "system", "content": SYSTEM_SURGEON_PROMPT}]
    messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_text})

    MAX_TURNS = 8
    turn = 0

    while turn < MAX_TURNS:
        turn += 1
        payload = {
            "model": "gemini-3.8-flash-high",
            "messages": messages,
            "temperature": 0.2
        }

        try:
            req = urllib.request.Request(
                LLM_PROXY_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                assistant_reply = data["choices"][0]["message"]["content"]
        except Exception as e:
            log(f"[BRAIN ERROR turn {turn}] {e}")
            return f"❌ Antigravity Brain bağlantı hatası: {e}"

        tool_call = extract_tool_call(assistant_reply)
        if not tool_call:
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": assistant_reply})
            CONVERSATION_HISTORY[chat_id] = history
            return assistant_reply

        tool_name = tool_call.get("tool", "")
        params = tool_call.get("params", {})

        param_summary = str(params.get("cmd") or params.get("path") or params.get("action") or "")[:40]
        step_note = f"⚙️ <i>[Adım {turn}/{MAX_TURNS}] <b>{tool_name}</b>: <code>{param_summary}</code></i>"
        send_msg(chat_id, step_note)

        tool_output = execute_agent_tool(tool_name, params, chat_id)
        trimmed = tool_output[:3500] if len(tool_output) > 3500 else tool_output

        messages.append({"role": "assistant", "content": assistant_reply})
        messages.append({
            "role": "user",
            "content": f"[TOOL_RESULT for {tool_name}]:\n{trimmed}\n\nLütfen sonucu değerlendirip sonraki adımı belirle veya nihai raporu sun."
        })

    return "⚠️ Maksimum cerrahi adım sınırına (8 adım) ulaşıldı."


# ── MENUS & KEYBOARDS ─────────────────────────────────────────────────────────
def get_main_menu_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "🚀 Hibrit Sistem Durumu", "callback_data": "menu_status"},
                {"text": "📸 Masaüstü Ekranı", "callback_data": "menu_screenshot"}
            ],
            [
                {"text": "🤖 Pablo Node Sağlık", "callback_data": "menu_pablo_health"},
                {"text": "🛡️ Guardian Doğrula", "callback_data": "menu_guardian_verify"}
            ],
            [
                {"text": "🔄 Pablo Yeniden Başlat", "callback_data": "menu_pablo_restart"}
            ]
        ]
    }


# ── MESSAGE DISPATCHER ────────────────────────────────────────────────────────
def handle_update(update: dict):
    # 1. Callback Queries
    if "callback_query" in update:
        cb = update["callback_query"]
        cb_id = cb["id"]
        from_id = cb["from"]["id"]
        data = cb.get("data", "")

        if from_id not in AUTHORIZED_CHATS:
            answer_callback(cb_id, "Yetkisiz kullanıcı.")
            return

        if data == "menu_status":
            answer_callback(cb_id, "Durum sorgulanıyor...")
            send_msg(from_id, get_system_status(), get_main_menu_keyboard())
        elif data == "menu_screenshot":
            answer_callback(cb_id, "Ekran görüntüsü alınıyor...")
            res = tool_windows_screenshot(from_id)
            if "ERROR" in res:
                send_msg(from_id, f"⚠️ {res}", get_main_menu_keyboard())
        elif data == "menu_pablo_health":
            answer_callback(cb_id, "Pablo sorgulanıyor...")
            w = check_windows_status()
            if w["online"]:
                send_msg(from_id, f"🟢 <b>PABLO SAĞLIK RAPORU:</b>\n<pre>{json.dumps(w, indent=2)}</pre>", get_main_menu_keyboard())
            else:
                send_msg(from_id, "🔴 <b>PABLO ÇEVRİMDIŞI:</b> Lenovo masaüstü kapalı veya uyku modunda.", get_main_menu_keyboard())
        elif data == "menu_guardian_verify":
            answer_callback(cb_id, "Guardian taranıyor...")
            res = tool_guardian_verify()
            send_msg(from_id, f"🛡️ <b>GUARDIAN RAPORU:</b>\n<pre>{res[:3500]}</pre>", get_main_menu_keyboard())
        elif data == "menu_pilot_status":
            answer_callback(cb_id, "Pilot durumu okunuyor...")
            res = tool_pilot_action("status")
            send_msg(from_id, f"🧪 <b>FAZ 4 PİLOT DURUMU:</b>\n<pre>{res[:3500]}</pre>", get_main_menu_keyboard())
        elif data == "menu_pilot_approve":
            answer_callback(cb_id, "Pilot onaylanıyor...")
            res = tool_pilot_action("approve")
            send_msg(from_id, f"✅ <b>PİLOT ONAYI:</b>\n<pre>{res[:3500]}</pre>", get_main_menu_keyboard())
        elif data == "menu_pilot_run":
            answer_callback(cb_id, "Pilot seansı başlatılıyor...")
            send_msg(from_id, "▶️ <b>Faz 4 Canlı Pilot Seansı Başlatılıyor...</b>")
            res = tool_pilot_action("run")
            send_msg(from_id, f"📊 <b>SEANS SONUCU:</b>\n<pre>{res[:3500]}</pre>", get_main_menu_keyboard())
        elif data == "menu_pablo_restart":
            answer_callback(cb_id, "Pablo yeniden başlatılıyor...")
            res = tool_pablo_action("restart")
            send_msg(from_id, f"🔄 <b>PABLO YENİDEN BAŞLATILDI:</b>\n<pre>{res[:3500]}</pre>", get_main_menu_keyboard())
        elif data == "menu_jeff_uptime":
            answer_callback(cb_id, "Jeff sorgulanıyor...")
            res = tool_jeff_shell("uptime && free -h")
            send_msg(from_id, f"🐧 <b>JEFF DURUMU:</b>\n<pre>{res[:3500]}</pre>", get_main_menu_keyboard())
        return

    # 2. Messages
    if "message" not in update:
        return

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    from_user = msg.get("from", {}).get("username", "Bilinmeyen")
    text = msg.get("text", "").strip()

    if chat_id not in AUTHORIZED_CHATS:
        log(f"[GÜVENLİK ENGELİ] Yetkisiz erişim teşebbüsü: id={chat_id}, user={from_user}, text={text}")
        send_msg(chat_id, "⛔ <b>Erişim Engellendi:</b> Bu bot yalnızca Bilal Ergene'nin yetkisine tahsis edilmiştir.")
        return

    log(f"[MESAJ] Bilal ({chat_id}): {text}")

    if not text:
        return

    cmd_lower = text.lower()
    if cmd_lower in ("/start", "/menu", "/help"):
        welcome = (
            "🛸 <b>ANTIGRAVITY 7/24 HİBRİT KONTROL PANELİ & OTONOM CERRAH</b>\n"
            "────────────────────────\n"
            "Bilal Bey hoş geldiniz! Sisteminiz <b>Jeff Linux (7/24 Kesintisiz)</b> ve <b>Lenovo Pablo Node</b> hibrit mimarisiyle devrededir.\n\n"
            "<b>7/24 Kesintisiz Güvence:</b>\n"
            "• Bilgisayarınız kapalı veya uykuda olsa dahi bu bot <b>asla kapanmaz</b>.\n"
            "• Jeff sunucusu üzerindeki tüm sistem ve kod ameliyatlarını yürütebilirsiniz.\n"
            "• Bilgisayarınızı açtığınız an Pablo Node otomatik olarak devreye girer.\n\n"
            "<b>Hızlı Komutlar:</b>\n"
            "• <code>/status</code> - Jeff ve Windows Pablo çift düğümlü durum raporu\n"
            "• <code>/screenshot</code> - Canlı Windows masaüstü görüntüsü\n"
            "• <code>/pablo restart</code> - Pablo Node'u yeniden başlat\n"
            "• <code>/guardian verify</code> - Baseline doğrula\n"
            "• <code>/cmd [komut]</code> - Windows üzerinde komut koştur\n"
            "• <code>/ssh [komut]</code> - Jeff Linux üzerinde komut koştur\n"
            "• <code>/clear</code> - Sohbet hafızasını temizle\n\n"
            "<i>Veya doğrudan doğal dille Türkçe talimat verin!</i>"
        )
        send_msg(chat_id, welcome, get_main_menu_keyboard())
        return

    elif cmd_lower == "/status":
        send_msg(chat_id, get_system_status(), get_main_menu_keyboard())
        return

    elif cmd_lower in ("/screenshot", "/ss"):
        send_msg(chat_id, "📸 Masaüstü görüntüsü alınıyor...")
        res = tool_windows_screenshot(chat_id)
        if "ERROR" in res:
            send_msg(chat_id, f"⚠️ {res}", get_main_menu_keyboard())
        return

    elif cmd_lower.startswith("/guardian"):
        send_msg(chat_id, "🛡️ Guardian baseline taranıyor...")
        res = tool_guardian_verify()
        send_msg(chat_id, f"<pre>{res[:3500]}</pre>", get_main_menu_keyboard())
        return

    elif cmd_lower.startswith("/pilot"):
        sub = text[6:].strip().lower()
        if sub == "approve":
            send_msg(chat_id, "✅ Pilot onaylanıyor...")
            res = tool_pilot_action("approve")
            send_msg(chat_id, f"<pre>{res[:3500]}</pre>", get_main_menu_keyboard())
        elif sub in ("run", "start", "baslat"):
            send_msg(chat_id, "▶️ Canlı pilot oturumu başlatılıyor...")
            res = tool_pilot_action("run")
            send_msg(chat_id, f"<pre>{res[:3500]}</pre>", get_main_menu_keyboard())
        elif sub in ("dry_run", "simulasyon"):
            send_msg(chat_id, "🧪 Pilot simülasyonu çalıştırılıyor...")
            res = tool_pilot_action("dry_run")
            send_msg(chat_id, f"<pre>{res[:3500]}</pre>", get_main_menu_keyboard())
        else:
            res = tool_pilot_action("status")
            send_msg(chat_id, f"🧪 <b>FAZ 4 PİLOT DURUMU:</b>\n<pre>{res[:3500]}</pre>", get_main_menu_keyboard())
        return

    elif cmd_lower.startswith("/pablo"):
        sub = text[6:].strip().lower()
        if sub in ("restart", "yeniden"):
            send_msg(chat_id, "🔄 Pablo yeniden başlatılıyor...")
            res = tool_pablo_action("restart")
            send_msg(chat_id, f"<pre>{res}</pre>", get_main_menu_keyboard())
        else:
            w = check_windows_status()
            if w["online"]:
                send_msg(chat_id, f"🤖 <b>Pablo Sağlık:</b>\n<pre>{json.dumps(w, indent=2)}</pre>", get_main_menu_keyboard())
            else:
                send_msg(chat_id, "🔴 <b>Pablo Çevrimdışı:</b> Lenovo masaüstü kapalı.", get_main_menu_keyboard())
        return

    elif cmd_lower.startswith("/cmd "):
        sh_cmd = text[5:].strip()
        send_msg(chat_id, f"⚙️ Windows komutu yürütülüyor: <code>{sh_cmd}</code>")
        res = tool_windows_shell(sh_cmd)
        send_msg(chat_id, f"<pre>{res[:3500]}</pre>")
        return

    elif cmd_lower.startswith("/ssh "):
        ssh_c = text[5:].strip()
        send_msg(chat_id, f"🐧 Jeff bash yürütülüyor: <code>{ssh_c}</code>")
        res = tool_jeff_shell(ssh_c)
        send_msg(chat_id, f"<pre>{res[:3500]}</pre>")
        return

    elif cmd_lower == "/clear":
        CONVERSATION_HISTORY[chat_id] = []
        send_msg(chat_id, "🧹 Sohbet hafızası temizlendi Bilal Bey.")
        return

    # Doğal Dil ile Cerrahi Operasyon & Ajan Döngüsü
    send_msg(chat_id, "⚡ <i>Antigravity 7/24 Hibrit Cerrah devrede, operasyon inceleniyor...</i>")
    reply = call_antigravity_brain(text, chat_id)
    send_msg(chat_id, reply, get_main_menu_keyboard())


# ── LONG-POLLING DAEMON ───────────────────────────────────────────────────────
def main_poll_loop():
    log("=" * 65)
    log("🛸 ANTIGRAVITY 24/7 HYBRID TELEGRAM CONTROLLER STARTED ON JEFF")
    log(f"Bot Token: {BOT_TOKEN[:10]}... | Yetkili: {AUTHORIZED_CHATS}")
    log(f"Windows Node URL: {WINDOWS_NODE_URL}")
    log("=" * 65)

    # Başlangıç bildirimi
    send_msg(
        AUTHORIZED_CHATS[0],
        "🛸 <b>Antigravity 7/24 Hibrit Cerrahi Sistemi Devrede!</b>\n"
        "Bot şu an <b>Jeff Linux sunucusu (7/24 Aktif)</b> üzerinden çalışmaktadır.\n"
        "Bilgisayarınız kapalı olsa dahi bana buradan dilediğiniz zaman ulaşabilirsiniz.",
        get_main_menu_keyboard()
    )

    offset = None
    consecutive_errors = 0

    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=25"
            if offset:
                url += f"&offset={offset}"

            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if data.get("ok"):
                consecutive_errors = 0
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    try:
                        handle_update(update)
                    except Exception as he:
                        log(f"[HANDLER ERROR] {he}")
            else:
                consecutive_errors += 1
                time.sleep(2)

        except urllib.error.URLError as ue:
            consecutive_errors += 1
            log(f"[POLL NETWORK WARN] {ue}")
            time.sleep(min(15, consecutive_errors * 2))
        except Exception as e:
            consecutive_errors += 1
            log(f"[POLL CRITICAL ERROR] {e}")
            time.sleep(min(15, consecutive_errors * 2))


if __name__ == "__main__":
    main_poll_loop()
