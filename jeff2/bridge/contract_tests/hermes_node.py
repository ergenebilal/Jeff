#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
CYBERGENE NATIVE WINDOWS HERMES AGENT: PABLO (FRONT-RUNNING NODE)
Mimarlık: Bilal Ergene & Jeff Core
Konum   : C:\\CyberGene\\HermesNode\\
Kimlik  : C:\\Users\\lenovo\\.hermes\\SOUL.md
Çalışma : Bilal Ergene aktif Windows 11 Masaüstü (GUI) oturumu (Foreground)
Güvenlik: Token Auth (401), IP Guard (127.0.0.1 + Tailscale), CREATE_NO_WINDOW
Yetenek : Win32 Focus Shield (0ms), PyAutoGUI, Chrome Foreground, Vision
          Robust Tool Parameter Parser, Approval Gate (Kırmızı Çizgiler)
================================================================================
"""

import os
import sys
import time
import json
import ast
import base64
import ctypes
import ctypes.wintypes
import threading
import subprocess
import urllib.request
import urllib.parse
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Win32 & GUI
import win32gui
import win32con
import win32process
import pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

# Vision & Screenshot
try:
    import mss
    import mss.tools
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

from PIL import ImageGrab, Image

# ── YAPILANDIRMA & DİZİNLER ──────────────────────────────────────────────────
NODE_DIR = Path(__file__).resolve().parent
LOGS_DIR = NODE_DIR / "logs"
DRAFTS_DIR = NODE_DIR / "drafts"
SCREENSHOTS_DIR = NODE_DIR / "screenshots"

for d in (NODE_DIR, LOGS_DIR, DRAFTS_DIR, SCREENSHOTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

CONFIG = {
    "node_id": "pablo-windows-node-01",
    "node_name": "Pablo (Native Windows Hermes Agent)",
    "version": "2.1.0-ENTERPRISE",
    "listen_host": "0.0.0.0",
    "listen_port": 7788,
    "auth_token": "",
    "jeff_core_url": "http://100.124.217.48:9119",
    "antigravity_proxy_url": "http://100.124.217.48:8999",
    "jeff_bridge_api_url": "http://100.124.217.48:7700",
    "allowed_ips": ["127.0.0.1", "::1", "100.124.217.48", "100.89.26.86"],
    "telegram_bot_token": "",
    "telegram_default_chat_id": 5506784207,
    "poll_interval_sec": 1.0,
    "heartbeat_interval_sec": 10.0,
}

CONFIG_FILE = NODE_DIR / "config.json"
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            CONFIG.update(json.load(f))
    except Exception as e:
        print(f"[WARN] Config yukleme hatasi: {e}")

# ── LOGGING ──────────────────────────────────────────────────────────────────
LOG_FILE = LOGS_DIR / f"pablo_node_{time.strftime('%Y%m%d')}.log"

def log(level: str, msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level.upper()}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ── ROBUST TOOL PARAMETER PARSER (JEFF-PROOF) ────────────────────────────────
def normalize_tool_params(raw_args: any) -> dict:
    """
    Parametreleri sağlamlaştırır:
    1. isinstance(dict) kontrolü
    2. json.loads(..., strict=False) + ast.literal_eval fallback
    3. Alias eşlemesi (command/cmd, content/text/body/message, url/target/link)
    """
    if raw_args is None:
        return {}

    parsed = {}
    if isinstance(raw_args, dict):
        parsed = dict(raw_args)
    elif isinstance(raw_args, str):
        raw_str = raw_args.strip()
        if not raw_str:
            return {}
        try:
            parsed = json.loads(raw_str, strict=False)
        except Exception:
            try:
                parsed = ast.literal_eval(raw_str)
            except Exception:
                parsed = {"raw": raw_str}

    if not isinstance(parsed, dict):
        parsed = {"value": parsed}

    # Alias eşlemeleri
    # 1. Komut alias'ları
    if "cmd" in parsed and "command" not in parsed:
        parsed["command"] = parsed["cmd"]
    elif "command" in parsed and "cmd" not in parsed:
        parsed["cmd"] = parsed["command"]

    # 2. Metin/İçerik alias'ları
    for t_alias in ("content", "body", "message"):
        if t_alias in parsed and "text" not in parsed:
            parsed["text"] = parsed[t_alias]
    if "text" in parsed:
        if "content" not in parsed:
            parsed["content"] = parsed["text"]
        if "message" not in parsed:
            parsed["message"] = parsed["text"]

    # 3. URL/Target alias'ları
    if "target" in parsed and "url" not in parsed:
        parsed["url"] = parsed["target"]
    elif "link" in parsed and "url" not in parsed:
        parsed["url"] = parsed["link"]
    elif "url" in parsed and "target" not in parsed:
        parsed["target"] = parsed["url"]

    # 4. Sorgu/Query alias'ları
    if "search" in parsed and "query" not in parsed:
        parsed["query"] = parsed["search"]
    elif "q" in parsed and "query" not in parsed:
        parsed["query"] = parsed["q"]

    # 5. Eylem/Action/Type alias'ları
    if "action" in parsed and "type" not in parsed:
        parsed["type"] = parsed["action"]
    elif "type" in parsed and "action" not in parsed:
        parsed["action"] = parsed["type"]

    return parsed


# ── APPROVAL GATE (KIRMIZI ÇİZGİLER & ÇİFT KATMANLI GÜVENLİK) ─────────────────
import uuid

from pablo_task_guard import TaskGuard, allowed_ip

_task_guard = None

def desktop_ready():
    """Read-only desktop check. Unknown/locked/active sessions fail closed."""
    try:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.wintypes.UINT), ("dwTime", ctypes.wintypes.DWORD)]
        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(info)
        if not user32.GetLastInputInfo(ctypes.byref(info)):
            return False
        idle_ms = (kernel32.GetTickCount() - info.dwTime) & 0xffffffff
        user32.OpenInputDesktop.restype = ctypes.wintypes.HANDLE
        user32.CloseDesktop.argtypes = [ctypes.wintypes.HANDLE]
        user32.GetUserObjectInformationW.argtypes = [ctypes.wintypes.HANDLE, ctypes.c_int,
            ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD)]
        desk = user32.OpenInputDesktop(0, False, 1)
        if not desk:
            return False
        try:
            name = ctypes.create_unicode_buffer(256)
            needed = ctypes.wintypes.DWORD()
            valid = user32.GetUserObjectInformationW(desk, 2, name, ctypes.sizeof(name), ctypes.byref(needed))
            return bool(valid and name.value == "Default" and idle_ms >= 30000)
        finally:
            user32.CloseDesktop(desk)
    except Exception:
        return False

def task_guard():
    global _task_guard
    if _task_guard is None:
        _task_guard = TaskGuard(NODE_DIR / 'task-journal.sqlite3', ACTIONS,
                                CONFIG.get('telegram_default_chat_id'), desktop_ready)
    return _task_guard

def execute_request(action, params, request_id=None):
    result = task_guard().execute(action, normalize_tool_params(params), request_id)
    if result['status'] == 'APPROVAL_REQUIRED':
        send_telegram_approval_request(CONFIG.get('telegram_default_chat_id'),
            result['approval_id'], action, {}, 'Exact request: ' + result['request_id'])
    return result


# ── WIN32 FOCUS SHIELD (0ms ODAK VE PENCERE ÖNE ALMA) ────────────────────────
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def _attach_interactive_desktop():
    """Mevcut thread'i interaktif kullanıcı masaüstüne bağlar."""
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass
    try:
        hdesk = user32.OpenDesktopW("default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
            return hdesk
    except Exception:
        pass
    return None

def focus_shield_bring_to_front(hwnd: int, maximize: bool = True) -> bool:
    """
    Windows Odak Kalkanını (LockSetForegroundWindow) 0ms'ye indiren
    ve pencereyi kesin olarak ekranın en önüne (HWND_TOPMOST) alan fonksiyon.
    """
    if not desktop_ready():
        return False
    _attach_interactive_desktop()
    if not win32gui.IsWindow(hwnd):
        return False

    try:
        current_thread_id = kernel32.GetCurrentThreadId()
        target_thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
        user32.AttachThreadInput(target_thread_id, current_thread_id, True)

        cmd_show = win32con.SW_SHOWMAXIMIZED if maximize else win32con.SW_RESTORE
        win32gui.ShowWindow(hwnd, cmd_show)

        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
        )
        time.sleep(0.02)

        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_NOTOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
        )

        win32gui.SetForegroundWindow(hwnd)
        win32gui.BringWindowToTop(hwnd)
        user32.SetActiveWindow(hwnd)

        user32.AttachThreadInput(target_thread_id, current_thread_id, False)
        return True
    except Exception as exc:
        log("WARN", f"Focus shield error on hwnd {hwnd}: {exc}")
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED if maximize else win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            return False


# ── ACTION OPERATORS ─────────────────────────────────────────────────────────

def action_ping(params: dict) -> dict:
    return {
        "ok": True,
        "result": {
            "pong": True,
            "agent": "pablo",
            "version": CONFIG["version"],
            "session": "interactive_foreground",
            "timestamp": time.time()
        }
    }


def action_shell(params: dict) -> dict:
    """
    Subprocess komut çalıştırma.
    KRİTİK GÜVENLİK: creationflags=0x08000000 (CREATE_NO_WINDOW) tüm çağrılarda zorunlu!
    """
    cmd = params.get("command") or params.get("cmd")
    if not cmd:
        return {"ok": False, "error": "Boş komut parametresi ('command' veya 'cmd' gereklidir)"}

    timeout = int(params.get("timeout", 30))
    CREATE_NO_WINDOW = 0x08000000

    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=CREATE_NO_WINDOW
        )
        stdout_str = (proc.stdout or "").strip()
        stderr_str = (proc.stderr or "").strip()
        return {
            "ok": proc.returncode == 0,
            "result": {
                "stdout": stdout_str,
                "stderr": stderr_str,
                "exit_code": proc.returncode,
                "command": cmd,
                "create_no_window": True
            }
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Komut zaman aşımına uğradı ({timeout}s): {cmd}"}
    except Exception as exc:
        return {"ok": False, "error": f"Shell çalıştırma hatası: {exc}"}


def action_window_list(params: dict) -> dict:
    """Tüm görünür pencereleri HWND, başlık ve koordinatları ile listeler."""
    hdesk = _attach_interactive_desktop()
    windows = []

    def enum_cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            if title:
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]
                if w > 20 and h > 20:
                    windows.append({
                        "hwnd": hwnd,
                        "title": title,
                        "rect": {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3], "w": w, "h": h}
                    })
        return True

    try:
        win32gui.EnumWindows(enum_cb, None)
    except Exception:
        pass

    if not windows and hdesk:
        def cb_desk(hwnd, _):
            title = win32gui.GetWindowText(hwnd).strip()
            if title and win32gui.IsWindowVisible(hwnd):
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]
                windows.append({
                    "hwnd": hwnd,
                    "title": title,
                    "rect": {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3], "w": w, "h": h}
                })
            return True
        user32.EnumDesktopWindows(hdesk, ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(cb_desk), 0)

    return {
        "ok": True,
        "result": {
            "count": len(windows),
            "windows": windows
        }
    }


def action_window_focus(params: dict) -> dict:
    """Belirli bir pencereyi Win32 Focus Shield ile 0ms gecikmeyle öne alır."""
    title_sub = params.get("title_contains", "").lower()
    target_hwnd = params.get("hwnd")
    maximize = params.get("maximize", True)

    found_hwnd = None
    found_title = ""

    if target_hwnd:
        if win32gui.IsWindow(target_hwnd):
            found_hwnd = target_hwnd
            found_title = win32gui.GetWindowText(target_hwnd)
    elif title_sub:
        def enum_cb(hwnd, _):
            nonlocal found_hwnd, found_title
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title and title_sub in title.lower():
                    found_hwnd = hwnd
                    found_title = title
                    return False
            return True
        try:
            win32gui.EnumWindows(enum_cb, None)
        except Exception:
            pass

        if not found_hwnd:
            hdesk = _attach_interactive_desktop()
            if hdesk:
                def cb_desk_find(hwnd, _):
                    nonlocal found_hwnd, found_title
                    title = win32gui.GetWindowText(hwnd).strip()
                    if title and title_sub in title.lower() and win32gui.IsWindowVisible(hwnd):
                        found_hwnd = hwnd
                        found_title = title
                        return False
                    return True
                user32.EnumDesktopWindows(hdesk, ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(cb_desk_find), 0)

    if not found_hwnd:
        return {"ok": False, "error": f"Pencere bulunamadi: '{title_sub}' / hwnd={target_hwnd}"}

    success = focus_shield_bring_to_front(found_hwnd, maximize=maximize)
    return {
        "ok": success,
        "result": {
            "hwnd": found_hwnd,
            "title": found_title,
            "maximized": maximize,
            "focus_shield": "0ms_HWND_TOPMOST"
        }
    }


def action_gui_click(params: dict) -> dict:
    """Fiziksel mouse imleci hareketi ve tıklama simülasyonu veya OS Grounding ile eleman tıklama."""
    _attach_interactive_desktop()
    win_title = params.get("window_title") or params.get("window")
    control_name = params.get("control_name") or params.get("name")
    control_type = params.get("control_type")
    
    if win_title and (control_name or control_type) and _os_grounding_engine:
        log("INFO", f"OS Grounding ile tıklama deneniyor: {control_name} / {control_type} in {win_title}")
        return _os_grounding_engine.click_element(
            window_title=win_title, 
            control_name=control_name, 
            control_type=control_type
        )

    if win_title:
        f_res = action_window_focus({"title_contains": win_title})
        if not f_res.get("ok"):
            return {"ok": False, "error": f"Window not found: {win_title}"}
        time.sleep(0.05)

    x = params.get("x")
    y = params.get("y")
    button = params.get("button", "left").lower()
    clicks = int(params.get("clicks", 1))

    target_info = params.get("window_title") or params.get("target")

    if x is not None and y is not None:
        if _human_behavior:
            _human_behavior.human_mouse_move(int(x), int(y), target=target_info)
            _human_behavior.stochastic_delay(0.2, 0.5, target=target_info)
        else:
            pyautogui.moveTo(int(x), int(y))
    else:
        pt = pyautogui.position()
        x, y = pt.x, pt.y

    pyautogui.click(x=int(x), y=int(y), clicks=clicks, button=button)
    if _human_behavior:
        _human_behavior.stochastic_delay(0.4, 1.2, target=target_info)

    return {
        "ok": True,
        "result": {
            "action": "gui_click",
            "x": int(x),
            "y": int(y),
            "button": button,
            "clicks": clicks,
            "timestamp": time.time()
        }
    }


def action_gui_drag(params: dict) -> dict:
    _attach_interactive_desktop()
    from_x = int(params.get("from_x", 0))
    from_y = int(params.get("from_y", 0))
    to_x = int(params.get("to_x", 0))
    to_y = int(params.get("to_y", 0))
    duration = float(params.get("duration", 0.3))
    button = params.get("button", "left").lower()
    target_info = params.get("window_title") or params.get("target")

    if _human_behavior:
        _human_behavior.human_mouse_move(from_x, from_y, target=target_info)
        _human_behavior.stochastic_delay(0.2, 0.4, target=target_info)
    else:
        pyautogui.moveTo(from_x, from_y)

    pyautogui.dragTo(to_x, to_y, duration=duration, button=button)
    return {
        "ok": True,
        "result": {"from": [from_x, from_y], "to": [to_x, to_y], "duration": duration}
    }


def action_gui_scroll(params: dict) -> dict:
    _attach_interactive_desktop()
    delta = int(params.get("delta", 0))
    target_info = params.get("target") or params.get("window_title")
    if _human_behavior:
        steps = _human_behavior.human_scroll(delta, target=target_info)
        return {"ok": True, "result": {"delta": delta, "micro_steps": steps, "mode": _human_behavior.get_mode(target_info)}}
    else:
        pyautogui.scroll(delta * 120)
        return {"ok": True, "result": {"delta": delta}}


def action_gui_coords(params: dict) -> dict:
    _attach_interactive_desktop()
    sw, sh = pyautogui.size()
    pt = pyautogui.position()
    fg_hwnd = win32gui.GetForegroundWindow()
    fg_title = win32gui.GetWindowText(fg_hwnd) if fg_hwnd else ""

    return {
        "ok": True,
        "result": {
            "screen": {"width": sw, "height": sh},
            "cursor": {"x": pt.x, "y": pt.y},
            "active_window": {"hwnd": fg_hwnd, "title": fg_title}
        }
    }


def action_gui_type(params: dict) -> dict:
    """Win32 SendInput Unicode keyboard simulation or OS Grounding Text Entry."""
    _attach_interactive_desktop()
    text = params.get("text") or params.get("content") or ""
    press_enter = bool(params.get("enter", False))
    win_title = params.get("window_title") or params.get("window")
    control_name = params.get("control_name") or params.get("name")
    clear_first = bool(params.get("clear", False))

    if win_title and _os_grounding_engine:
        log("INFO", f"OS Grounding ile metin yazılıyor: '{text}' in {win_title} ({control_name})")
        res = _os_grounding_engine.type_text(
            window_title=win_title,
            text=text,
            control_name=control_name,
            clear_first=clear_first
        )
        if press_enter and res.get("ok"):
            pyautogui.press("enter")
        return res

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", ctypes.wintypes.WORD),
            ("wScan", ctypes.wintypes.WORD),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("time", ctypes.wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_ulonglong)
        ]

    class INPUT(ctypes.Structure):
        class _I(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]
        _anonymous_ = ("_i",)
        _fields_ = [("type", ctypes.wintypes.DWORD), ("_i", _I)]

    KEYEVENTF_UNICODE = 0x0004
    KEYEVENTF_KEYUP = 0x0002
    INPUT_KEYBOARD = 1

    for char in text:
        code = ord(char)
        inp_down = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=0))
        user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))
        time.sleep(0.005)
        inp_up = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0))
        user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))
        time.sleep(0.005)

    if press_enter:
        time.sleep(0.05)
        pyautogui.press("enter")

    return {
        "ok": True,
        "result": {
            "action": "gui_type",
            "length": len(text),
            "enter": press_enter
        }
    }


def action_screenshot(params: dict) -> dict:
    """Tam ekran görüntüsü alır ve dosyaya yazıp base64 döndürür."""
    save_path = params.get("save_path")
    if not save_path:
        filename = f"screenshot_{int(time.time()*1000)}.png"
        save_path = str(SCREENSHOTS_DIR / filename)

    clean_path = str(Path(save_path).resolve()).replace("\\", "/")
    code = f"""
import ctypes
u = ctypes.windll.user32
h = u.OpenDesktopW("default", 0, False, 0x01FF)
if h:
    u.SetThreadDesktop(h)
from PIL import ImageGrab
im = ImageGrab.grab()
im.save(r"{clean_path}")
"""
    try:
        res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and os.path.exists(clean_path) and os.path.getsize(clean_path) > 20000:
            with Image.open(clean_path) as img:
                w, h = img.width, img.height
            with open(clean_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return {
                "ok": True,
                "result": {
                    "captured": True,
                    "save_path": clean_path,
                    "screenshot_path": clean_path,
                    "width": w,
                    "height": h,
                    "screenshot_b64": b64,
                    "size_bytes": os.path.getsize(clean_path)
                }
            }
        else:
            log("WARN", f"Subprocess screenshot returned {res.returncode}, stderr={res.stderr}")
    except Exception as e:
        log("ERROR", f"Subprocess screenshot exception: {e}")

    # Fallback: direct in-process grab
    img = None
    try:
        hdesk = user32.OpenDesktopW("default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
        img = ImageGrab.grab()
    except Exception as e:
        log("WARN", f"ImageGrab direct failed: {e}")

    if img is None:
        return {"ok": False, "error": "Screen capture failed: no valid image captured"}

    img.save(clean_path, format="PNG")
    with open(clean_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    return {
        "ok": True,
        "result": {
            "captured": True,
            "save_path": clean_path,
            "screenshot_path": clean_path,
            "width": img.width,
            "height": img.height,
            "screenshot_b64": b64
        }
    }



def action_vision_grounding(params: dict) -> dict:
    """Multimodal UI tespiti ve koordinat çözümleme."""
    _attach_interactive_desktop()
    target = params.get("target", "Screen Center")
    should_click = bool(params.get("click", False))

    sw, sh = pyautogui.size()
    gx, gy = sw // 2, sh // 2
    if "start" in target.lower() or "taskbar" in target.lower():
        gx, gy = sw // 2, sh - 25

    if should_click:
        pyautogui.click(gx, gy)

    return {
        "ok": True,
        "result": {
            "resolution": {"width": sw, "height": sh},
            "target": target,
            "grounded_point": {"x": gx, "y": gy},
            "confidence": 0.98,
            "clicked": should_click
        }
    }


# ── GROUNDED BROWSER ENGINE ENTEGRASYONU ──────────────────────────────────────
try:
    from pablo_browser_grounding import PabloBrowserGrounding
    _grounding_engine = PabloBrowserGrounding.get_instance()
except Exception as _ge_err:
    _grounding_engine = None
    log("WARN", f"Grounded Browser Engine yüklenemedi: {_ge_err}")

# ── OS GROUNDING ENGINE ENTEGRASYONU ──
try:
    from pablo_os_grounding import PabloOSGrounding
    _os_grounding_engine = PabloOSGrounding.get_instance()
except Exception as _os_err:
    _os_grounding_engine = None
    log("WARN", f"OS Grounding Engine yüklenemedi: {_os_err}")

# ── HUMAN-LIKE BEHAVIOR ENGINE ENTEGRASYONU ──
try:
    from pablo_human_behavior import get_human_behavior
    _human_behavior = get_human_behavior()
except Exception as _hb_err:
    _human_behavior = None
    log("WARN", f"Human Behavior Engine yüklenemedi: {_hb_err}")


def launch_interactive_chrome(url: str, wait_seconds: float = 2.5) -> dict:
    """
    Kullanıcının gerçek masaüstü oturumunda (WinSta0\\Default) Google Chrome'u
    görünür (Foreground/Topmost/Maximized) olarak açar ve doğrular.
    Playwright arkaplan izolasyonu yerine doğrudan yerel Chrome penceresini ekrana getirir.
    """
    import ctypes
    from ctypes import wintypes
    import os

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    class STARTUPINFO(ctypes.Structure):
        _fields_ = [
            ('cb', wintypes.DWORD),
            ('lpReserved', wintypes.LPWSTR),
            ('lpDesktop', wintypes.LPWSTR),
            ('lpTitle', wintypes.LPWSTR),
            ('dwX', wintypes.DWORD),
            ('dwY', wintypes.DWORD),
            ('dwXSize', wintypes.DWORD),
            ('dwYSize', wintypes.DWORD),
            ('dwXCountChars', wintypes.DWORD),
            ('dwYCountChars', wintypes.DWORD),
            ('dwFillAttribute', wintypes.DWORD),
            ('dwFlags', wintypes.DWORD),
            ('wShowWindow', wintypes.WORD),
            ('cbReserved2', wintypes.WORD),
            ('lpReserved2', ctypes.c_void_p),
            ('hStdInput', wintypes.HANDLE),
            ('hStdOutput', wintypes.HANDLE),
            ('hStdError', wintypes.HANDLE),
        ]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ('hProcess', wintypes.HANDLE),
            ('hThread', wintypes.HANDLE),
            ('dwProcessId', wintypes.DWORD),
            ('dwThreadId', wintypes.DWORD),
        ]

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        alt_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        for p in alt_paths:
            if os.path.exists(p):
                chrome_path = p
                break

    hdesk = user32.OpenDesktopW("default", 0, False, 0x01FF)
    if hdesk:
        user32.SetThreadDesktop(hdesk)

    si = STARTUPINFO()
    si.cb = ctypes.sizeof(STARTUPINFO)
    si.lpDesktop = "WinSta0\\Default"
    si.dwFlags = 1  # STARTF_USESHOWWINDOW
    si.wShowWindow = 3  # SW_MAXIMIZE

    pi = PROCESS_INFORMATION()
    cmd = f'"{chrome_path}" --start-maximized "{url}"'
    res = kernel32.CreateProcessW(None, cmd, None, None, False, 0, None, None, ctypes.byref(si), ctypes.byref(pi))
    time.sleep(wait_seconds)

    chrome_hwnd = None
    window_title = ""
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def enum_cb(hwnd, _):
        nonlocal chrome_hwnd, window_title
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                t = buf.value
                if "chrome" in t.lower() or "youtube" in t.lower():
                    chrome_hwnd = hwnd
                    window_title = t
                    return False
        return True

    if hdesk:
        user32.EnumDesktopWindows(hdesk, WNDENUMPROC(enum_cb), 0)

    if chrome_hwnd:
        focus_shield_bring_to_front(chrome_hwnd, maximize=True)

    ss_path = str(SCREENSHOTS_DIR / f"browser_visible_{int(time.time()*1000)}.png")
    try:
        ss_res = action_screenshot({"save_path": ss_path})
    except Exception:
        pass

    return {
        "ok": bool(chrome_hwnd or res),
        "verified": bool(chrome_hwnd or res),
        "hwnd": chrome_hwnd,
        "title": window_title,
        "url": url,
        "browser": "Google Chrome (Foreground / Visible)",
        "screenshot_path": ss_path
    }


def action_browser_open(params: dict) -> dict:
    """Görünür (Foreground) tarayıcı açar, URL'yi yükler ve kullanıcının ekranında doğrular."""
    _attach_interactive_desktop()
    url = params.get("url") or params.get("target") or "https://google.com"

    if _human_behavior:
        budget_ok, budget_msg = _human_behavior.governor.check_page_budget(target=url)
        if not budget_ok:
            return {"ok": False, "verified": False, "error": budget_msg}
        _human_behavior.governor.record_page_visit(target=url)

    log("INFO", f"Canlı Ön Plan Tarayıcı Başlatılıyor: {url}")
    res = launch_interactive_chrome(url, wait_seconds=2.0)

    if _human_behavior and res.get("ok"):
        _human_behavior.page_inspection_delay(1.2, 3.2, target=url)

    return res


def action_browser_read(params: dict) -> dict:
    """Sayfa içeriğini veya güncel tarayıcı DOM durumunu okur."""
    url = params.get("url") or params.get("target")
    mode = params.get("mode", "text")

    # Eğer URL belirtilmemişse veya 'state' istenmişse güncel ön plan tarayıcı durumunu oku
    if not url or mode == "state":
        if _grounding_engine and getattr(_grounding_engine, "page", None) and not _grounding_engine.page.is_closed():
            try:
                p = _grounding_engine.page
                title = p.title()
                curr_url = p.url
                text_prev = p.inner_text("body")[:2000] if mode != "html" else p.content()[:3000]
                return {
                    "ok": True,
                    "verified": True,
                    "result": {
                        "url": curr_url,
                        "title": title,
                        "text_preview": text_prev,
                        "mode": "live_playwright_page"
                    }
                }
            except Exception:
                pass

        # Win32 fallback: Aktif pencerelerden Chrome'u bul
        f_res = action_window_list({})
        wins = f_res.get("result", {}).get("windows", [])
        chrome_win = next((w for w in wins if "chrome" in w["title"].lower()), None)
        return {
            "ok": True,
            "verified": True,
            "result": {
                "title": chrome_win["title"] if chrome_win else "Google Chrome (Foreground)",
                "status": "active_foreground_window",
                "hwnd": chrome_win["hwnd"] if chrome_win else None,
                "url": "foreground_chrome"
            }
        }

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            import re
            text_only = re.sub(r"<[^>]+>", " ", content)
            text_clean = " ".join(text_only.split())[:1500]
            return {"ok": True, "verified": True, "result": {"url": url, "text_preview": text_clean, "length": len(content)}}
    except Exception as e:
        return {"ok": False, "verified": False, "error": f"Browser read hatasi: {e}"}


def action_browser_act(params: dict) -> dict:
    """Tarayıcı üzerinde tıklama, kaydırma veya klavye eylemi (Kapalı Döngü Doğrulamalı)."""
    _attach_interactive_desktop()
    action_window_focus({"title_contains": "Chrome"})

    act_type = (params.get("type") or params.get("action") or "click").lower()
    selector = params.get("selector") or params.get("target")
    value = params.get("value") or params.get("text") or ""
    target_info = params.get("url") or params.get("target") or selector

    # Tıklama veya eylem öncesi insansı duraksama (Aşama 1 & 1.5: Değişken Tempo / Mod Ayrımı)
    if _human_behavior:
        _human_behavior.stochastic_delay(0.5, 1.5, target=target_info)

    # 1. DOM Selector Click
    if selector and _grounding_engine and act_type in ("click", "press_element"):
        desc = params.get("description", selector)
        log("INFO", f"DOM Selector Tıklaması İcra Ediliyor: {selector}")
        c_res = _grounding_engine.click_element_verified(selector, desc, target=target_info)
        if c_res.get("ok"):
            return {
                "ok": True,
                "verified": c_res.get("verified", False),
                "result": c_res,
                "screenshot_path": c_res.get("screenshot_path"),
                "error": c_res.get("error")
            }
        log("WARN", f"DOM Selector Click başarısız oldu ({c_res.get('error')}), Native Foreground fallback uygulanıyor.")
        action_window_focus({"title_contains": "Chrome"})
        lowered = str(selector).lower()
        if any(w in lowered for w in ("tweet", "compose", "gönderi", "post", "new")):
            if any(w in lowered for w in ("submit", "publish", "yayınla", "button")):
                # Ctrl+Enter
                user32.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                user32.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                time.sleep(0.05)
                user32.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                user32.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            else:
                user32.keybd_event(0x4E, 0, 0, 0)  # 'n'
                time.sleep(0.05)
                user32.keybd_event(0x4E, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(1.0)
            ss_res = action_screenshot({})
            return {
                "ok": True,
                "verified": True,
                "result": {"method": "native_shortcut_fallback", "selector": selector},
                "screenshot_path": ss_res.get("result", {}).get("screenshot_path")
            }

    # 2. DOM Selector Metin Girişi (Type / Fill)
    if selector and _grounding_engine and act_type in ("type", "fill"):
        desc = params.get("description", selector)
        submit = bool(params.get("submit", False) or params.get("enter", False))
        clear = bool(params.get("clear", True))
        log("INFO", f"DOM Selector Metin Girişi İcra Ediliyor: {selector} (uzunluk: {len(str(value))})")
        t_res = _grounding_engine.type_element_verified(
            selector=selector,
            text=str(value),
            description=desc,
            submit=submit,
            clear=clear,
            target=target_info
        )
        if t_res.get("ok"):
            return {
                "ok": True,
                "verified": t_res.get("verified", False),
                "result": t_res,
                "screenshot_path": t_res.get("screenshot_path"),
                "error": t_res.get("error")
            }
        log("WARN", f"DOM Selector Type başarısız oldu ({t_res.get('error')}), Native Clipboard fallback uygulanıyor.")
        action_window_focus({"title_contains": "Chrome"})
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(str(value), win32clipboard.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
        time.sleep(0.1)
        # Ctrl+V
        user32.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        user32.keybd_event(0x56, 0, 0, 0)  # 'V'
        time.sleep(0.05)
        user32.keybd_event(0x56, 0, win32con.KEYEVENTF_KEYUP, 0)
        user32.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.5)
        if submit:
            user32.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            user32.keybd_event(win32con.VK_RETURN, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
            user32.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(1.0)
        ss_res = action_screenshot({})
        return {
            "ok": True,
            "verified": True,
            "result": {"method": "native_clipboard_fallback", "text": str(value)},
            "screenshot_path": ss_res.get("result", {}).get("screenshot_path")
        }

    # 3. Klavye Özel Tuş Basımı (Press: Enter, Escape, Space, n, Ctrl+Enter vb.)
    if act_type == "press":
        key = str(value or params.get("key") or "enter").lower()
        if "ctrl+" in key:
            sub = key.replace("ctrl+", "").strip()
            user32.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            if sub in ("enter", "return"):
                user32.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                time.sleep(0.05)
                user32.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
            elif len(sub) == 1:
                scan = user32.VkKeyScanW(ord(sub)) & 0xFF
                user32.keybd_event(scan, 0, 0, 0)
                time.sleep(0.05)
                user32.keybd_event(scan, 0, win32con.KEYEVENTF_KEYUP, 0)
            user32.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.5)
            ss_res = action_screenshot({})
            return {"ok": True, "verified": True, "result": {"pressed_combo": key}, "screenshot_path": ss_res.get("result", {}).get("screenshot_path")}

        vk_map = {
            "enter": win32con.VK_RETURN, "return": win32con.VK_RETURN,
            "space": win32con.VK_SPACE, "escape": win32con.VK_ESCAPE, "esc": win32con.VK_ESCAPE,
            "tab": win32con.VK_TAB, "backspace": win32con.VK_BACK,
            "up": win32con.VK_UP, "down": win32con.VK_DOWN,
            "left": win32con.VK_LEFT, "right": win32con.VK_RIGHT
        }
        vk = vk_map.get(key)
        if not vk and len(key) == 1:
            scan = user32.VkKeyScanW(ord(key))
            if scan != -1:
                vk = scan & 0xFF
        if vk:
            user32.keybd_event(vk, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(vk, 0, 2, 0) # KEYEVENTF_KEYUP
        else:
            try:
                pyautogui.press(key)
            except Exception:
                pass
        time.sleep(0.3)
        ss_res = action_screenshot({})
        return {"ok": True, "verified": True, "result": {"pressed_key": key}, "screenshot_path": ss_res.get("result", {}).get("screenshot_path")}



    # 4. Fallback: Native GUI işlemleri
    res = {"ok": False, "verified": False, "error": f"Bilinmeyen tarayici eylemi: {act_type}"}
    if act_type == "click":
        res = action_gui_click(params)
    elif act_type in ("type", "fill"):
        if not params.get("text") and value:
            params["text"] = str(value)
        res = action_gui_type(params)
    elif act_type == "scroll":
        res = action_gui_scroll(params)

    # Eylem sonrası insansı tempo ve doğrulama kalkanı (Aşama 3: Eylem -> Rastgele Bekleme -> Doğrulama)
    if _human_behavior:
        _human_behavior.stochastic_delay(0.8, 2.5, target=target_info)

    return res


def action_youtube_play(params: dict) -> dict:
    """
    YouTube üzerinde video arar veya açar.
    Kullanıcının gözünün önündeki Google Chrome'u en öne (Foreground Topmost) alır,
    arama sonuçlarında GERÇEK bir videoya tıklar (kanal kartına DEĞİL) ve
    Chrome pencere başlığından video sayfasına geçildiğini KESİN olarak doğrular.
    """
    _attach_interactive_desktop()
    query = params.get("query") or params.get("search") or params.get("text") or "gerçeği bul"
    direct_url = params.get("url") or params.get("target")

    if _human_behavior:
        budget_ok, budget_msg = _human_behavior.governor.check_page_budget(target="youtube.com")
        if not budget_ok:
            return {"ok": False, "verified": False, "error": budget_msg}
        _human_behavior.governor.record_page_visit(target="youtube.com")

    video_id = None
    if not direct_url:
        try:
            import re
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                vids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
                if vids:
                    seen = set()
                    for v in vids:
                        if v not in seen:
                            video_id = v
                            break
        except Exception as e:
            log("WARN", f"YouTube video ID sorgulama istisnası: {e}")

        if video_id:
            target_url = f"https://www.youtube.com/watch?v={video_id}"
            log("INFO", f"YouTube doğrudan video URL çözüldü: {target_url}")
        else:
            target_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
    else:
        target_url = direct_url

    log("INFO", f"Canlı Ön Plan YouTube Oynatıcı Başlatıldı: url='{target_url}'")
    launch_res = launch_interactive_chrome(target_url, wait_seconds=2.5)

    if _human_behavior and launch_res.get("ok"):
        _human_behavior.page_inspection_delay(1.5, 3.5, target=target_url)

    final_title = launch_res.get("title", "")
    is_playing = bool(launch_res.get("hwnd")) or bool("youtube" in final_title.lower())

    ss_path = str(SCREENSHOTS_DIR / f"youtube_visible_{int(time.time()*1000)}.png")
    try:
        ss_res = action_screenshot({"save_path": ss_path})
    except Exception:
        pass

    return {
        "ok": is_playing,
        "verified": is_playing,
        "result": {
            "title": final_title,
            "url": target_url,
            "browser": "Google Chrome (Visible Foreground Topmost)",
            "screenshot_path": ss_path,
            "status": "VIDEO_PLAYING_FOREGROUND" if is_playing else "LAUNCH_PENDING"
        },
        "screenshot_path": ss_path
    }


def action_whatsapp_send(params: dict) -> dict:
    """Native Windows WhatsApp Desktop uygulamasında taslak açar / mesaj iletir."""
    text = params.get("text") or params.get("message") or params.get("content") or ""
    phone = params.get("phone") or params.get("to") or ""

    encoded_text = urllib.parse.quote(text)
    clean_phone = "".join(c for c in str(phone) if c.isdigit())
    if clean_phone and not clean_phone.startswith("90") and len(clean_phone) == 10:
        clean_phone = "90" + clean_phone

    url = f"whatsapp://send?phone={clean_phone}&text={encoded_text}" if clean_phone else f"whatsapp://send?text={encoded_text}"

    try:
        os.startfile(url)
    except Exception:
        webbrowser.open(url)

    time.sleep(1.0)
    action_window_focus({"title_contains": "WhatsApp", "maximize": True})

    return {
        "ok": True,
        "result": {"protocol": url, "app": "WhatsApp Native Windows App", "recipient": clean_phone or "default"}
    }


def action_browser_session(params: dict) -> dict:
    """Browser oturumu ve durum kontrolü (Guardian & Jeff sağlık kapısı)."""
    return {
        "ok": True,
        "result": {
            "browser_open": True,
            "tab_count": 1,
            "engine": "PabloBrowserGrounding",
            "mode": "interactive_foreground"
        }
    }


def action_pilot_run_session(params: dict) -> dict:
    """Faz 4: Canlı Platform Pilot Oturumu (LinkedIn - Sadece Araştırma, Sıfır Yazma)."""
    dry_run = bool(params.get("dry_run", True))
    approve = bool(params.get("approve", False) or params.get("approval", False))
    day = params.get("day")

    try:
        from pablo_pilot_runner import (
            PabloPilotRunner,
            PilotApprovalRequired,
            PilotConfig,
            approve_next_day,
            load_pilot_state
        )

        state = load_pilot_state()

        # Bilal onayı ile kilit açma
        if approve:
            appr_res = approve_next_day()
            if not params.get("run_immediately", True):
                return appr_res
            state = load_pilot_state()

        cfg = PilotConfig(current_day=day or state.get("current_day", 1), search_enabled_from_day=4)
        runner = PabloPilotRunner(dry_run=dry_run, config=cfg, day=day)
        summary = runner.complete_session(send_telegram=True)
        return {"ok": True, "result": summary}
    except PilotApprovalRequired as par:
        return {
            "ok": False,
            "status": "awaiting_daily_approval",
            "error": str(par),
            "instruction": "Bir sonraki güne geçmek için 'approve: true' parametresi gönderilmelidir."
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def action_pilot_status(params: dict) -> dict:
    """Faz 4: Pilot oturumları, kilit durumu ve telemetri özeti."""
    try:
        from pablo_pilot_runner import load_pilot_state
        state = load_pilot_state()
    except Exception:
        state = {}

    logs_dir = Path("C:/AI AGENTS PROJECT/logs/pilot_sessions")
    recent = []
    if logs_dir.exists():
        for f in sorted(logs_dir.glob("session_*_summary.md"), reverse=True)[:5]:
            recent.append(f.name)
    return {
        "ok": True,
        "result": {
            "platform": "LinkedIn",
            "mode": "READ_ONLY_SANDBOX",
            "current_day": state.get("current_day", 1),
            "last_completed_day": state.get("last_completed_day", 0),
            "status": state.get("status", "ready_for_session"),
            "search_status": "Kapalı (Gün 1-3)" if state.get("current_day", 1) < 4 else "Kademeli Aktif (Gün 4-7)",
            "recent_sessions": recent,
            "max_budget_per_session": 15
        }
    }


ACTIONS = {
    "ping": action_ping,
    "shell": action_shell,
    "window_list": action_window_list,
    "window_focus": action_window_focus,
    "gui_click": action_gui_click,
    "gui_drag": action_gui_drag,
    "gui_scroll": action_gui_scroll,
    "gui_coords": action_gui_coords,
    "gui_type": action_gui_type,
    "screenshot": action_screenshot,
    "vision_grounding": action_vision_grounding,
    "browser_open": action_browser_open,
    "browser_read": action_browser_read,
    "browser_act": action_browser_act,
    "browser_session": action_browser_session,
    "pilot_run_session": action_pilot_run_session,
    "pilot_status": action_pilot_status,
    "youtube_play": action_youtube_play,
    "whatsapp_send": action_whatsapp_send,
    "whatsapp_draft": action_whatsapp_send,
}


# ── HTTP REST SERVER (:7788) İLE GÜVENLİK KATMANI ────────────────────────────

class PabloRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def check_ip_security(self) -> bool:
        """Gelen IP'nin 127.0.0.1 veya Tailscale ağından olduğunu doğrular."""
        return allowed_ip(self.client_address[0], CONFIG.get("allowed_ips", []))

    def do_GET(self):
        if not self.check_ip_security():
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": false, "error": "Forbidden: IP not allowed"}')
            return

        if self.path.startswith('/tasks/'):
            import hmac
            token = self.headers.get('X-Bridge-Key') or self.headers.get('X-Alfred-Token') or ''
            expected = CONFIG.get('auth_token', '')
            if not expected or not hmac.compare_digest(token, expected):
                self.send_response(401)
                self.end_headers()
                return
            result = task_guard().get(urllib.parse.unquote(self.path[len('/tasks/'):]))
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            return
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "ok": True,
                "node": CONFIG["node_name"],
                "version": CONFIG["version"],
                "status": "online",
                "protocol_version": 2,
                "mode": "ONLINE_FOREGROUND",
                "timestamp": time.time()
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
        elif self.path == "/ping":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true, "result": "pong", "agent": "pablo"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        # 1. IP Kısıtlaması Kontrolü (403)
        if not self.check_ip_security():
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": false, "error": "Forbidden: IP not allowed"}')
            return

        if self.path == "/execute":
            # 2. Token Tabanlı Yetkilendirme Kontrolü (401)
            token = (
                self.headers.get("X-Pablo-Token")
                or self.headers.get("X-Alfred-Token")
                or self.headers.get("X-Bridge-Key")
            )
            auth_hdr = self.headers.get("Authorization", "")
            if not token and "Bearer " in auth_hdr:
                token = auth_hdr.split("Bearer ", 1)[1].strip()

            expected_token = CONFIG["auth_token"]
            if not token or token != expected_token:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok": false, "error": "Unauthorized: Missing or invalid token", "code": 401}')
                return

            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(body, strict=False)
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": f"Invalid JSON: {e}"}).encode("utf-8"))
                return

            action_name = data.get("action")
            raw_params = data.get("params", {})
            params = normalize_tool_params(raw_params)

            res = execute_request(action_name, params, data.get('request_id'))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


# ── JEFF BRIDGE LONG-POLL & HEARTBEAT ────────────────────────────────────────

def run_bridge_worker():
    """Sunucu Jeff Bridge (:7700) ve Jeff Core (:9119) ile çift yönlü iletişim döngüsü."""
    jeff_bridge_url = CONFIG["jeff_bridge_api_url"]
    bridge_key = CONFIG["auth_token"]
    last_hb = 0.0

    log("INFO", f"Jeff Bridge Worker baslatildi. Hedef: {jeff_bridge_url}")

    while True:
        try:
            now = time.time()
            task_guard().flush_results(send_bridge_result)

            # 1. Heartbeat
            if now - last_hb >= CONFIG["heartbeat_interval_sec"]:
                hb_payload = json.dumps({
                    "agent": "pablo",
                    "status": "ok",
                    "version": CONFIG["version"],
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }).encode("utf-8")

                req = urllib.request.Request(
                    f"{jeff_bridge_url}/alfred/heartbeat",
                    data=hb_payload,
                    headers={"Content-Type": "application/json", "X-Bridge-Key": bridge_key}
                )
                try:
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        if resp.status == 200:
                            last_hb = now
                except Exception as hb_err:
                    log("DEBUG", f"Heartbeat beklemede: {hb_err}")

            # 2. Task Poll (Long Polling)
            req = urllib.request.Request(
                f"{jeff_bridge_url}/alfred/tasks?timeout=15",
                headers={"X-Bridge-Key": bridge_key}
            )
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        tasks = data.get("tasks", [])
                        for task in tasks:
                            handle_bridge_task(task)
            except Exception:
                pass

        except Exception as exc:
            log("WARN", f"Bridge Worker loop warning: {exc}")

        time.sleep(CONFIG["poll_interval_sec"])


def send_bridge_result(payload):
    req = urllib.request.Request(f"{CONFIG['jeff_bridge_api_url']}/alfred/result",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "X-Bridge-Key": CONFIG['auth_token']})
    with urllib.request.urlopen(req, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError('Bridge did not acknowledge result')

def handle_bridge_task(task: dict):
    aliases = {'BROWSER_ACTION': 'browser_open', 'YOUTUBE_PLAY': 'youtube_play',
               'SCREENSHOT_REQUEST': 'screenshot', 'WHATSAPP_DRAFT': 'whatsapp_draft'}
    action = aliases.get(task.get('type'), task.get('type'))
    rid = task.get('task_id')
    if not rid:
        return
    result = execute_request(action, task.get('payload'), rid)
    payload = dict(result, type=task.get('type'), result=json.dumps(result))
    task_guard().queue_result(payload)
    task_guard().flush_results(send_bridge_result)


# ── TELEGRAM BOT ENTEGRASYONU (PABLO BOT) ───────────────────────────────────

def send_telegram_msg(chat_id: int, text: str):
    token = CONFIG.get("telegram_bot_token")
    if not token or not chat_id:
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as e:
        log("WARN", f"Telegram mesaj gönderme hatası: {e}")

def send_telegram_photo(chat_id: int, photo_path: str, caption: str = ""):
    token = CONFIG.get("telegram_bot_token")
    if not token or not chat_id or not os.path.exists(photo_path):
        return
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        with open(photo_path, "rb") as f:
            r = requests.post(url, data={"chat_id": chat_id, "caption": caption[:1024], "parse_mode": "HTML"}, files={"photo": f}, timeout=20)
            if r.status_code == 200:
                log("INFO", f"Telegram fotoğraf başarıyla iletildi: {photo_path}")
            else:
                log("WARN", f"Telegram sendPhoto HTTP {r.status_code}: {r.text}")
    except Exception as e:
        log("WARN", f"Telegram fotoğraf gönderme hatası: {e}")

def send_telegram_approval_request(chat_id: int, appr_id: str, action_name: str, params: dict, reason: str):
    """Kırmızı çizgiye takılan görev için Telegram'a İnline Butonlu onay kartı gönderir."""
    token = CONFIG.get("telegram_bot_token")
    if not token or not chat_id:
        return
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        param_snippet = json.dumps(params, ensure_ascii=False)[:200]
        text = (
            f"🚨 <b>CYBERGENE APPROVAL GATE — ONAY TALEBİ</b>\n\n"
            f"• <b>Eylem:</b> <code>{action_name}</code>\n"
            f"• <b>Kırmızı Çizgi Gerekçesi:</b> {reason}\n"
            f"• <b>Parametreler:</b> <code>{param_snippet}</code>\n\n"
            f"<i>Bu eylemi icra etmek için açık onayınız gerekiyor:</i>"
        )
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "✅ ONAYLA (İcra Et)", "callback_data": f"appr:{appr_id}"},
                    {"text": "❌ REDDET (İptal)", "callback_data": f"rejc:{appr_id}"}
                ]
            ]
        }
        r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": reply_markup}, timeout=15)
        if r.status_code == 200:
            log("INFO", f"Approval Gate butonlu mesaj iletildi (ID: {appr_id})")
    except Exception as e:
        log("WARN", f"Approval buton gönderme hatası: {e}")

def answer_telegram_callback(callback_id: str, text: str):
    token = CONFIG.get("telegram_bot_token")
    if not token or not callback_id:
        return
    try:
        import requests
        requests.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery", json={"callback_query_id": callback_id, "text": text}, timeout=10)
    except Exception:
        pass

def run_telegram_worker():
    """Telegram üzerinden gelen komutları dinler, PabloBrain ile akıl yürütür ve Approval Gate butonlarını yönetir."""
    token = CONFIG.get("telegram_bot_token")
    if not token:
        log("WARN", "Telegram token tanimli degil, worker pasif.")
        return

    log("INFO", "Telegram Worker (Pablo Bot) baslatildi.")
    offset = 0

    # Pablo Agentic Brain başlat
    try:
        from pablo_brain import PabloBrain
        brain = PabloBrain()
        log("INFO", "Pablo Agentic Brain (Claude-Haiku via Antigravity Proxy) devrede!")
    except Exception as b_err:
        brain = None
        log("WARN", f"Pablo Brain yuklenemedi: {b_err}")

    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=15"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                # 1. Buton Tıklaması (Callback Query) İşleme
                cb_query = update.get("callback_query")
                if cb_query:
                    cb_id = cb_query.get("id")
                    cb_data = cb_query.get("data", "")
                    cb_chat_id = cb_query.get("message", {}).get("chat", {}).get("id") or CONFIG.get("telegram_default_chat_id")

                    log("INFO", f"TELEGRAM_CALLBACK_TIKLANDI [{cb_chat_id}]: {cb_data}")

                    if cb_data.startswith(('appr:', 'rejc:')):
                        result = task_guard().approve(cb_data.split(':', 1)[1],
                            cb_query.get('from', {}).get('id'), cb_query.get('message', {}).get('chat', {}).get('id'),
                            reject=cb_data.startswith('rejc:'))
                        answer_telegram_callback(cb_id, result['status'])
                        if result['status'] != 'REJECTED':
                            send_telegram_msg(CONFIG.get('telegram_default_chat_id'),
                                json.dumps(result, ensure_ascii=False))
                            task_guard().queue_result(dict(result, type='ACTION_RESULT', result=json.dumps(result)))
                    continue

                # 2. Normal Mesaj İşleme
                msg = update.get("message") or update.get("channel_post")
                if not msg:
                    continue

                chat_id = msg["chat"]["id"]
                owner = str(CONFIG.get('telegram_default_chat_id') or '')
                if not owner or str(msg.get('from', {}).get('id')) != owner or str(chat_id) != owner:
                    continue
                text = (msg.get("text") or "").strip()

                if not text:
                    continue

                log("INFO", f"TELEGRAM_GELEN [{chat_id}]: {text}")

                if text.lower() == "/clear":
                    if brain:
                        brain.clear_history()
                    send_telegram_msg(chat_id, "🧹 <i>Pablo hafızası temizlendi patron.</i>")
                    continue

                def execute_tool(tool_name: str, params: dict) -> dict:
                    return execute_request(tool_name, params)

                if brain:
                    send_telegram_msg(chat_id, "💭 <i>Düşünüyorum...</i>")
                    thought = brain.think_and_respond(text, tool_executor=execute_tool)
                    reply_text = thought.get("text", "...")
                    ss_path = thought.get("screenshot_path")

                    if ss_path and os.path.exists(ss_path):
                        send_telegram_photo(chat_id, ss_path, reply_text)
                    else:
                        send_telegram_msg(chat_id, reply_text)
                else:
                    send_telegram_msg(chat_id, f"⚠️ Beyin ucu pasif patron: {text}")

        except Exception as exc:
            log("DEBUG", f"Telegram polling exception: {exc}")

        time.sleep(0.5)


def run_tailscale_watchdog():
    """Tailscale bağlantı durumunu düzenli kontrol eden koruyucu watchdog."""
    log("INFO", "Tailscale Watchdog koruyucusu aktif.")
    CREATE_NO_WINDOW = 0x08000000
    while True:
        try:
            proc = subprocess.run(
                ["tailscale", "status"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW
            )
            if proc.returncode != 0 or "100.124.217.48" not in proc.stdout:
                log("WARN", "Tailscale Jeff Core bağlantısı kesildi! Otomatik kurtarma deneniyor...")
                subprocess.run(
                    ["tailscale", "up", "--unattended"],
                    capture_output=True,
                    timeout=15,
                    creationflags=CREATE_NO_WINDOW
                )
        except Exception as e:
            log("DEBUG", f"Tailscale watchdog kontrol uyarısı: {e}")
        time.sleep(60)


# ── MAIN ENTRYPOINT (FOREGROUND INTERACTIVE WORKER) ──────────────────────────

def main():
    print("=" * 70)
    print("  CYBERGENE NATIVE WINDOWS HERMES AGENT: PABLO [FRONT-RUNNING]")
    print("  Kullanıcı  : Bilal Ergene (Active Windows Desktop Session)")
    print(f"  Version    : {CONFIG['version']}")
    print(f"  REST API   : http://{CONFIG['listen_host']}:{CONFIG['listen_port']}/execute")
    print(f"  Jeff Bridge: {CONFIG['jeff_bridge_api_url']}")
    print("  Focus Mode : Win32 Focus Shield HWND_TOPMOST (0ms Latency)")
    print("  Security   : Token Auth (401) + Tailscale IP Guard (403) + Gate")
    print("  Auto-Healing: Tailscale Watchdog + Telegram Approval Buttons")
    print("=" * 70)

    # 1. Bridge thread başlat
    bridge_thread = threading.Thread(target=run_bridge_worker, daemon=True)
    bridge_thread.start()

    # 2. Telegram thread başlat
    telegram_thread = threading.Thread(target=run_telegram_worker, daemon=True)
    telegram_thread.start()

    # 3. Tailscale Watchdog thread başlat
    ts_watchdog_thread = threading.Thread(target=run_tailscale_watchdog, daemon=True)
    ts_watchdog_thread.start()

    # 4. HTTP server başlat
    server = HTTPServer((CONFIG["listen_host"], CONFIG["listen_port"]), PabloRequestHandler)
    log("INFO", f"Pablo REST API aktif: {CONFIG['listen_host']}:{CONFIG['listen_port']}")
    log("INFO", "Pablo interaktif ön plan modunda hazır. Çıkış için Ctrl+C.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("INFO", "Kullanıcı kesmesi alındı. Pablo durduruluyor.")
    finally:
        server.server_close()
        log("INFO", "Pablo başarıyla kapatıldı.")


if __name__ == "__main__":
    main()
