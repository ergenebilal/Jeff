#!/usr/bin/env python3
"""Voice mode manager — toggles between text and voice response modes.

Usage:
  voice_mode_manager.py status            — check current mode
  voice_mode_manager.py on                — enable voice mode
  voice_mode_manager.py off               — disable voice mode
  voice_mode_manager.py speak "<text>"    — generate voice response via Chatterbox

When voice mode is ON, all assistant responses auto-generate a voice message.
Voice mode state is stored in ~/.hermes/voice_mode.json.
"""

import json
import os
import sys
import subprocess
import re
import time

STATE_FILE = os.path.expanduser("~/.hermes/voice_mode.json")
VOICE_BRIDGE = os.path.expanduser("~/.hermes/voice_bridge_v2.py")
CACHE_DIR = os.path.expanduser("~/.hermes/voice_cache/")
CHATTERBOX_DAEMON = os.path.expanduser("~/.hermes/scripts/chatterbox_daemon.py")
JARVIS_VENV_PYTHON = os.path.expanduser("~/jarvis-ergeneai/.venv/bin/python3")

DEFAULT_STATE = {
    "voice_mode": False,
    "active_voice": "jeff",  # jeff = Chatterbox Puck Clone
    "last_response_ogg": None,
}


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            try:
                return {**DEFAULT_STATE, **json.load(f)}
            except json.JSONDecodeError:
                return dict(DEFAULT_STATE)
    return dict(DEFAULT_STATE)


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _daemon_alive():
    try:
        result = subprocess.run(
            ["pgrep", "-f", CHATTERBOX_DAEMON],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


def _start_daemon():
    if not os.path.exists(CHATTERBOX_DAEMON) or not os.path.exists(JARVIS_VENV_PYTHON):
        return False
    try:
        os.makedirs(os.path.expanduser("~/.hermes/logs"), exist_ok=True)
        env = os.environ.copy()
        env.setdefault("CHATTERBOX_MAX_NEW_TOKENS", "180")
        with open(os.path.expanduser("~/.hermes/logs/chatterbox_daemon.out.log"), "a") as out_log, open(
            os.path.expanduser("~/.hermes/logs/chatterbox_daemon.err.log"), "a"
        ) as err_log:
            subprocess.Popen(
                [JARVIS_VENV_PYTHON, CHATTERBOX_DAEMON],
                stdout=out_log,
                stderr=err_log,
                start_new_session=True,
                env=env,
            )
        for _ in range(240):
            if _daemon_alive():
                return True
            time.sleep(0.25)
    except Exception:
        return False
    return False


def _stop_daemon():
    try:
        subprocess.run(["pkill", "-f", CHATTERBOX_DAEMON], capture_output=True, text=True, timeout=5, check=False)
    except Exception:
        pass


def speak(text, state):
    """Generate voice response, return OGG path or None."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    # Clean text for filename
    safe = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ]', '_', text[:40])
    out_path = os.path.join(CACHE_DIR, f"response_{safe}.ogg")

    try:
        result = subprocess.run(
            ["python3", VOICE_BRIDGE, text],
            capture_output=True, text=True, timeout=360
        )
        if result.returncode == 0:
            # Bridge prints the OGG path on last line
            lines = result.stdout.strip().split("\n")
            ogg_path = lines[-1] if lines else None
            if ogg_path and os.path.exists(ogg_path):
                state["last_response_ogg"] = ogg_path
                save_state(state)
                return ogg_path
        # Fallback: check cache
        if os.path.exists(out_path):
            state["last_response_ogg"] = out_path
            save_state(state)
            return out_path
        return None
    except Exception as e:
        print(f"Voice gen error: {e}", file=sys.stderr)
        return None


def main():
    state = load_state()

    if len(sys.argv) < 2:
        cmd = "status"
    else:
        cmd = sys.argv[1]

    if cmd == "status":
        mode = "SESLİ" if state["voice_mode"] else "YAZILI"
        print(f"Mod: {mode}")
        print(f"Ses: {state['active_voice']}")
        print(f"Son OGG: {state.get('last_response_ogg', 'yok')}")
        return

    if cmd == "on":
        state["voice_mode"] = True
        save_state(state)
        _start_daemon()
        print("✅ Ses modu AÇIK. Cevap verirken ses de göndereceğim.")
        return

    if cmd == "off":
        state["voice_mode"] = False
        save_state(state)
        _stop_daemon()
        print("✅ Ses modu KAPALI. Normal yazılı sohbet.")
        return

    if cmd == "speak" and len(sys.argv) > 2:
        text = sys.argv[2]
        ogg_path = speak(text, state)
        if ogg_path:
            print(f"MEDIA:{ogg_path}")
        else:
            print("Ses üretilemedi.")
        return

    print(f"Bilinmeyen komut: {cmd}")
    print("Kullanım: voice_mode_manager.py {status|on|off|speak '<text>'}")
    sys.exit(1)


if __name__ == "__main__":
    main()
