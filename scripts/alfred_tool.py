#!/usr/bin/env python3
"""
Alfred Client & CLI Tool for Jeff (Hermes)
Provides direct, low-latency execution of actions on Alfred (Windows laptop).

Usage (CLI):
  alfred ping
  alfred screenshot [--out /path/to/screen.png]
  alfred browser <url>
  alfred browser-act <action> [--target <target>] [--value <val>] [--screenshot] [-o <path>]
  alfred browser-read [mode] [--selector <sel>] [--query <query>] [-o <path>]
  alfred browser-session [status|list_tabs|new_tab|switch_tab|close] [--url <url>]
  alfred shell "<powershell-command>"
  alfred read <windows-path>
  alfred write <windows-path> "<content>"
  alfred ls <windows-path>
  alfred wa <phone> "<message>"
  alfred benchmark

Usage (Python):
  import alfred_tool as alfred
  res = alfred.ping()
  res = alfred.screenshot(save_as="/tmp/screen.png")
  res = alfred.shell("Get-Process | Select-Object -First 5")
"""

import os
import sys
import json
import time
import uuid
import base64
import argparse
import contextvars
try:
    from hermes_constants import get_hermes_home
except ImportError:
    sys.path.insert(0, '/opt/hermes')
    from hermes_constants import get_hermes_home
from jeff_task_evidence import atomic_json
request_context = contextvars.ContextVar('pablo_request', default=None)
last_response = contextvars.ContextVar('pablo_response', default=None)
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    print("requests library missing. Install via pip install requests", file=sys.stderr)
    sys.exit(1)

ALFRED_HOST = os.environ.get("ALFRED_HOST", "100.89.26.86")
ALFRED_PORT = int(os.environ.get("ALFRED_PORT", "7788"))
ALFRED_BASE_URL = f"http://{ALFRED_HOST}:{ALFRED_PORT}"
BRIDGE_KEY = os.environ.get("BRIDGE_KEY", "cybergene-bridge-2026")

_session: Optional[requests.Session] = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            "X-Alfred-Token": BRIDGE_KEY,
            "X-Bridge-Key": BRIDGE_KEY,
            "Content-Type": "application/json",
            "User-Agent": "JeffClient/3.0",
            "Connection": "keep-alive",
        })
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=0)
        _session.mount("http://", adapter)
    return _session


def is_online(timeout: float = 3.0) -> bool:
    try:
        r = get_session().get(f"{ALFRED_BASE_URL}/health", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def get_health(timeout: float = 3.0) -> Dict[str, Any]:
    try:
        r = get_session().get(f"{ALFRED_BASE_URL}/health", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"ok": False, "status": "offline", "error": str(exc)}


def execute(action: str, params: Optional[dict] = None, mode: str = "sync", timeout: float = 35.0, request_id: Optional[str] = None) -> Dict[str, Any]:
    req_id = request_id or request_context.get() or str(uuid.uuid4())
    payload = {'request_id': req_id, 'action': action, 'params': params or {}, 'mode': mode, 'timeout': timeout}
    journal = get_hermes_home() / 'pablo-requests' / (str(uuid.uuid5(uuid.NAMESPACE_URL, req_id)) + '.json')
    previous = json.loads(journal.read_text()) if journal.exists() else None
    if previous and (previous['request']['action'], previous['request']['params']) != (action, params or {}):
        return {'ok': False, 'status': 'CONFLICT', 'request_id': req_id, 'task_id': req_id, 'error': 'Request content changed'}
    t0 = time.time()
    atomic_json(journal, {'request': payload, 'response': {'status': 'IN_PROGRESS'}})
    try:
        session = get_session()
        if previous:
            # A transport timeout does not prove non-execution. Reconcile; never blindly replay.
            from urllib.parse import quote
            response = session.get(f"{ALFRED_BASE_URL}/tasks/{quote(req_id, safe='')}", timeout=timeout)
        else:
            response = session.post(f"{ALFRED_BASE_URL}/execute", json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or data.get('request_id') != req_id:
            data = {'ok': False, 'status': 'PROTOCOL_ERROR', 'error': 'Missing or mismatched request ID'}
        status = data.get('status', 'PROTOCOL_ERROR')
        data['ok'] = data.get('ok') is True and status == 'SUCCESS'
    except requests.exceptions.Timeout:
        data = {'ok': False, 'status': 'TIMEOUT', 'error': 'Execution outcome unknown; reconcile this request ID'}
    except requests.exceptions.ConnectionError:
        data = {'ok': False, 'status': 'OFFLINE', 'error': 'Pablo unavailable; request retained'}
    except Exception as exc:
        data = {'ok': False, 'status': 'ERROR', 'error': type(exc).__name__}
    data.update(request_id=req_id, task_id=req_id, client_rtt_ms=round((time.time()-t0)*1000, 2))
    atomic_json(journal, {'request': payload, 'response': data})
    last_response.set(data)
    return data


# ── High-Level Tool Methods ───────────────────────────────────────────────────

def ping(message: str = "ping") -> Dict[str, Any]:
    return execute("ping", {"message": message})


def screenshot(save_as: Optional[str] = None) -> Dict[str, Any]:
    res = execute("screenshot")
    if not res.get("ok"):
        return res

    result_data = res.get("result", {})
    if not result_data.get("captured"):
        return res

    b64 = result_data.get("screenshot_b64")
    if b64 and save_as:
        try:
            out_file = Path(save_as).resolve()
            out_file.parent.mkdir(parents=True, exist_ok=True)
            png_bytes = base64.b64decode(b64)
            out_file.write_bytes(png_bytes)
            result_data["saved_path"] = str(out_file)
            result_data["saved_bytes"] = len(png_bytes)
            # Remove base64 from return to keep output clean and fast
            del result_data["screenshot_b64"]
        except Exception as exc:
            result_data["save_error"] = str(exc)

    return res


def browser_open(url: str) -> Dict[str, Any]:
    return execute("browser_open", {"url": url})


def browser_act(
    action: str,
    target: str = "",
    value: Any = "",
    wait_ms: int = 800,
    timeout: int = 10000,
    screenshot: bool = False,
    tab_index: Optional[int] = None,
    save_as: Optional[str] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "action": action,
        "target": target,
        "value": value,
        "wait_ms": wait_ms,
        "timeout": timeout,
        "screenshot": str(screenshot).lower() if isinstance(screenshot, bool) else str(screenshot),
    }
    if tab_index is not None:
        params["tab_index"] = tab_index

    client_timeout = max((timeout / 1000.0) + (wait_ms / 1000.0) + 15.0, 35.0)
    res = execute("browser_act", params, timeout=client_timeout)

    if res.get("ok") and save_as:
        result_data = res.get("result", {})
        b64 = result_data.get("screenshot_b64")
        if b64:
            try:
                out_file = Path(save_as).resolve()
                out_file.parent.mkdir(parents=True, exist_ok=True)
                png_bytes = base64.b64decode(b64)
                out_file.write_bytes(png_bytes)
                result_data["saved_path"] = str(out_file)
                result_data["saved_bytes"] = len(png_bytes)
                del result_data["screenshot_b64"]
            except Exception as exc:
                result_data["save_error"] = str(exc)

    return res


def browser_read(
    mode: str = "text",
    selector: str = "body",
    query: str = "",
    schema: Optional[dict] = None,
    max_chars: int = 30000,
    save_as: Optional[str] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "mode": mode,
        "selector": selector,
        "query": query,
        "schema": schema or {},
        "max_chars": max_chars,
    }
    res = execute("browser_read", params, timeout=35.0)

    if res.get("ok") and save_as and mode == "screenshot":
        result_data = res.get("result", {})
        b64 = result_data.get("screenshot_b64")
        if b64:
            try:
                out_file = Path(save_as).resolve()
                out_file.parent.mkdir(parents=True, exist_ok=True)
                png_bytes = base64.b64decode(b64)
                out_file.write_bytes(png_bytes)
                result_data["saved_path"] = str(out_file)
                result_data["saved_bytes"] = len(png_bytes)
                del result_data["screenshot_b64"]
            except Exception as exc:
                result_data["save_error"] = str(exc)

    return res


def browser_session(
    action: str = "status",
    url: str = "",
    tab_index: int = 0,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "action": action,
    }
    if url:
        params["url"] = url
    if action == "switch_tab":
        params["tab_index"] = tab_index

    return execute("browser_session", params, timeout=35.0)


def shell(command: str, timeout: int = 30, cwd: Optional[str] = None, shell_type: str = "powershell") -> Dict[str, Any]:
    params = {"command": command, "timeout": timeout, "shell": shell_type}
    if cwd:
        params["cwd"] = cwd
    return execute("shell", params, timeout=timeout + 5)


def file_read(path: str, max_bytes: int = 10 * 1024 * 1024) -> Dict[str, Any]:
    return execute("file_read", {"path": path, "max_bytes": max_bytes})


def file_write(path: str, content: str, mode: str = "w") -> Dict[str, Any]:
    return execute("file_write", {"path": path, "content": content, "mode": mode})


def file_list(path: str = ".") -> Dict[str, Any]:
    return execute("file_list", {"path": path})


def whatsapp_draft(phone: str, text: str) -> Dict[str, Any]:
    return execute("whatsapp_draft", {"phone": phone, "text": text})


def openclaw_status() -> Dict[str, Any]:
    return execute("openclaw_status")


def window_list() -> Dict[str, Any]:
    return execute("window_list", {})


def window_focus(title_contains: str = "", hwnd: Optional[int] = None, maximize: bool = True) -> Dict[str, Any]:
    params: Dict[str, Any] = {"maximize": maximize}
    if title_contains:
        params["title_contains"] = title_contains
    if hwnd is not None:
        params["hwnd"] = hwnd
    return execute("window_focus", params)


def file_dialog_submit(paths: Any) -> Dict[str, Any]:
    if isinstance(paths, str):
        paths_list = [paths]
    elif isinstance(paths, list):
        paths_list = paths
    else:
        paths_list = [str(paths)]
    return execute("file_dialog_submit", {"paths": paths_list})


def execute_async(action: str, params: Optional[dict] = None) -> Dict[str, Any]:
    return execute(action, params, mode="async")


def get_job(job_id: str) -> Dict[str, Any]:
    try:
        r = get_session().get(f"{ALFRED_BASE_URL}/jobs/{job_id}", timeout=5)
        return r.json()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def cancel_job(job_id: str) -> Dict[str, Any]:
    try:
        r = get_session().post(f"{ALFRED_BASE_URL}/jobs/{job_id}/cancel", json={}, timeout=5)
        return r.json()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── Benchmark / Diagnostic ────────────────────────────────────────────────────

def benchmark(count: int = 5) -> Dict[str, Any]:
    times = []
    print(f"Benchmarking Jeff -> Alfred latency over Tailscale ({count} iterations)...")
    for i in range(count):
        t0 = time.time()
        res = ping(f"bench-{i}")
        dt = (time.time() - t0) * 1000
        if res.get("ok"):
            srv_ms = res.get("timing", {}).get("execution_ms", 0)
            net_rtt = round(dt - srv_ms, 2)
            times.append(dt)
            print(f"  [{i+1}/{count}] Total RTT: {dt:.2f} ms | Server Exec: {srv_ms:.2f} ms | Net Overhead: {net_rtt:.2f} ms")
        else:
            print(f"  [{i+1}/{count}] FAILED: {res.get('error')}")

    if times:
        avg = sum(times) / len(times)
        min_t = min(times)
        max_t = max(times)
        print(f"Results: Min = {min_t:.2f} ms | Avg = {avg:.2f} ms | Max = {max_t:.2f} ms")
        return {"min_ms": min_t, "avg_ms": avg, "max_ms": max_t, "count": len(times)}
    return {"error": "All benchmark pings failed"}


# ── CLI Interface ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Jeff Alfred Tool CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("ping", help="Ping Alfred")
    subparsers.add_parser("health", help="Check health of Alfred")
    subparsers.add_parser("benchmark", help="Run latency benchmark")

    p_scr = subparsers.add_parser("screenshot", help="Capture screenshot on Windows")
    p_scr.add_argument("-o", "--out", help="Save PNG to path on server", default=None)

    p_br = subparsers.add_parser("browser", help="Open URL on Windows")
    p_br.add_argument("url", help="URL to open")

    # browser-act (and browser_act)
    for cmd_name in ("browser-act", "browser_act"):
        p_bact = subparsers.add_parser(cmd_name, help="Perform browser action (click, fill, scroll, etc.)")
        p_bact.add_argument("act", help="Action (navigate, click, type, fill, press, hover, select, scroll, go_back, new_tab, switch_tab, close_tab, wait)")
        p_bact.add_argument("--target", default="", help="Target CSS selector or URL")
        p_bact.add_argument("--value", default="", help="Value string, text, key, or scroll pixels")
        p_bact.add_argument("--wait-ms", type=int, default=800, help="Wait time after action in ms")
        p_bact.add_argument("--timeout", type=int, default=10000, help="Timeout in ms")
        p_bact.add_argument("--screenshot", action="store_true", help="Capture screenshot after action")
        p_bact.add_argument("--tab-index", type=int, default=None, help="Tab index for switch_tab")
        p_bact.add_argument("-o", "--out", default=None, help="Save screenshot to local file if --screenshot")

    # browser-read (and browser_read)
    for cmd_name in ("browser-read", "browser_read"):
        p_bread = subparsers.add_parser(cmd_name, help="Read browser content (text, html, links, find, state, screenshot)")
        p_bread.add_argument("mode", nargs="?", default="text", choices=["text", "html", "links", "find", "state", "structured", "screenshot"], help="Read mode")
        p_bread.add_argument("--selector", default="body", help="CSS selector")
        p_bread.add_argument("--query", default="", help="Text query for find mode")
        p_bread.add_argument("--schema", default=None, help="JSON schema for structured mode")
        p_bread.add_argument("--max-chars", type=int, default=30000, help="Max characters to return")
        p_bread.add_argument("-o", "--out", default=None, help="Save PNG to path if mode is screenshot")

    # browser-session (and browser_session)
    for cmd_name in ("browser-session", "browser_session"):
        p_bsess = subparsers.add_parser(cmd_name, help="Manage browser session (status, list_tabs, new_tab, switch_tab, close)")
        p_bsess.add_argument("sess_action", nargs="?", default="status", choices=["status", "list_tabs", "new_tab", "switch_tab", "close"], help="Session action")
        p_bsess.add_argument("--url", default="", help="URL for new_tab")
        p_bsess.add_argument("--tab-index", type=int, default=0, help="Tab index for switch_tab")

    p_sh = subparsers.add_parser("shell", help="Run PowerShell/CMD command on Windows")
    p_sh.add_argument("cmd", help="Command string")
    p_sh.add_argument("--timeout", type=int, default=30, help="Timeout in seconds")
    p_sh.add_argument("--cwd", default=None, help="Working directory")
    p_sh.add_argument("--cmd-shell", action="store_true", help="Use cmd instead of powershell")

    p_read = subparsers.add_parser("read", help="Read file on Windows")
    p_read.add_argument("path", help="Windows file path")

    p_write = subparsers.add_parser("write", help="Write file on Windows")
    p_write.add_argument("path", help="Windows file path")
    p_write.add_argument("content", help="Content to write")

    p_ls = subparsers.add_parser("ls", help="List directory on Windows")
    p_ls.add_argument("path", nargs="?", default=".", help="Directory path")

    p_wa = subparsers.add_parser("wa", help="Draft WhatsApp message on Windows")
    p_wa.add_argument("phone", help="Phone number")
    p_wa.add_argument("message", help="Message text")

    subparsers.add_parser("windows", help="List open windows on Windows")

    p_foc = subparsers.add_parser("focus", help="Focus a window on Windows (Win32 Focus Shield)")
    p_foc.add_argument("title", help="Window title substring to match")
    p_foc.add_argument("--no-maximize", dest="maximize", action="store_false", default=True, help="Do not maximize window")

    p_dlg = subparsers.add_parser("upload_dialog", help="Submit file paths to Windows file dialog")
    p_dlg.add_argument("paths", nargs="+", help="File paths to submit")

    parser.add_argument('--request-id', help='Stable task identity; reuse to reconcile without replay')
    p_status = subparsers.add_parser('status', help='Reconcile a retained task without re-execution')
    p_status.add_argument('request_id')
    args = parser.parse_args()
    if args.request_id:
        request_context.set(args.request_id)
    if args.command == 'status':
        journal = get_hermes_home() / 'pablo-requests' / (str(uuid.uuid5(uuid.NAMESPACE_URL, args.request_id)) + '.json')
        if not journal.exists():
            print(json.dumps({'ok': False, 'status': 'NOT_FOUND', 'request_id': args.request_id}))
            return 1
        previous = json.loads(journal.read_text())['request']
        result = execute(previous['action'], previous['params'], request_id=args.request_id)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result.get('ok') else 1

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "ping":
        res = ping()
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "health":
        res = get_health()
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "benchmark":
        benchmark()
    elif args.command == "screenshot":
        res = screenshot(save_as=args.out)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "browser":
        res = browser_open(args.url)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command in ("browser-act", "browser_act"):
        res = browser_act(
            action=args.act,
            target=args.target,
            value=args.value,
            wait_ms=args.wait_ms,
            timeout=args.timeout,
            screenshot=args.screenshot,
            tab_index=args.tab_index,
            save_as=args.out,
        )
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command in ("browser-read", "browser_read"):
        schema_dict = None
        if args.schema:
            try:
                schema_dict = json.loads(args.schema)
            except Exception:
                schema_dict = {}
        res = browser_read(
            mode=args.mode,
            selector=args.selector,
            query=args.query,
            schema=schema_dict,
            max_chars=args.max_chars,
            save_as=args.out,
        )
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command in ("browser-session", "browser_session"):
        res = browser_session(
            action=args.sess_action,
            url=args.url,
            tab_index=args.tab_index,
        )
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "shell":
        sh_type = "cmd" if args.cmd_shell else "powershell"
        res = shell(args.cmd, timeout=args.timeout, cwd=args.cwd, shell_type=sh_type)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "read":
        res = file_read(args.path)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "write":
        res = file_write(args.path, args.content)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "ls":
        res = file_list(args.path)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "wa":
        res = whatsapp_draft(args.phone, args.message)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "windows":
        res = window_list()
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "focus":
        res = window_focus(title_contains=args.title, maximize=args.maximize)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "upload_dialog":
        res = file_dialog_submit(paths=args.paths)
        print(json.dumps(res, indent=2, ensure_ascii=False))

    return 0 if locals().get("res", {}).get("ok") is True else 1

if __name__ == "__main__":
    raise SystemExit(main())
