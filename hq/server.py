#!/usr/bin/env python3
"""ErgeneAI Komuta Merkezi backend. Localhost-only HTTP API."""

import json
import os
import shlex
import socket
import subprocess
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse


HQ = Path(__file__).resolve().parent
ROOT = HQ.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class HQAPIHandler(SimpleHTTPRequestHandler):
    _command_history = []

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._json_response(self._build_health())
        elif parsed.path == "/api/tokens":
            self._json_response(self._build_tokens())
        elif parsed.path == "/api/decisions":
            self._json_response(self._build_decisions())
        elif parsed.path == "/api/status":
            self._json_response(self._build_full_status())
        elif parsed.path == "/api/context/active":
            self._json_response(self._build_context_active())
        elif parsed.path == "/api/baseline/status":
            self._json_response(self._build_baseline())
        elif parsed.path == "/api/persona/status":
            self._json_response(self._build_persona_status())
        elif parsed.path == "/api/n8n/health":
            self._json_response(self._build_n8n_health())
        elif parsed.path == "/api/command-history":
            self._json_response({"commands": self._command_history[-10:]})
        elif parsed.path == "/api/dashboard/runs":
            self._json_response(self._build_dashboard_runs())
        elif parsed.path == "/api/dashboard/skills":
            self._json_response(self._build_dashboard_skills())
        elif parsed.path == "/api/dashboard/cron":
            self._json_response(self._build_dashboard_cron())
        elif parsed.path == "/api/dashboard/token-trends":
            self._json_response(self._build_dashboard_token_trends())
        elif parsed.path == "/api/dashboard/policy":
            self._json_response(self._build_dashboard_policy())
        elif parsed.path == "/api/dashboard/eval":
            self._json_response(self._build_dashboard_eval())
        elif parsed.path == "/api/dashboard/alarms":
            self._json_response(self._build_dashboard_alarms())
        elif parsed.path in {"", "/"}:
            self._serve_html()
        else:
            self._json_response({"error": "not_found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        data = self._read_json_body()
        if parsed.path == "/api/command":
            payload, status = _run_allowed_command(str(data.get("command", "")).strip())
            if status == 200:
                self._command_history.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "command": payload.get("command"),
                        "exit_code": payload.get("exit_code"),
                    }
                )
            self._json_response(payload, status)
        elif parsed.path == "/api/token-limit":
            payload, status = _handle_token_limit(data)
            self._json_response(payload, status)
        elif parsed.path == "/api/context/close":
            payload, status = self._handle_context_close(data)
            self._json_response(payload, status)
        elif parsed.path == "/api/n8n/write_enable":
            payload, status = self._handle_n8n_write_enable(data)
            self._json_response(payload, status)
        else:
            self._json_response({"error": "not_found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8889")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if not content_length:
            return {}
        try:
            raw = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(raw) if raw else {}
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8889")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def _serve_html(self):
        index = HQ / "index.html"
        if not index.exists():
            self._json_response({"error": "index.html not found"}, 500)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(index.read_bytes())

    @staticmethod
    def _build_health() -> dict:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "gateway": _systemd_active("hermes-gateway.service"),
                "embedding": _port_open("127.0.0.1", 8767),
                "headroom": _port_open("127.0.0.1", 8787),
                "n8n": _port_open("127.0.0.1", 5678),
            },
            "system": {
                "memory": _memory(),
                "disk": _disk(),
            },
        }

    @staticmethod
    def _build_tokens() -> dict:
        try:
            from brain.token import TokenGuard, get_budget_left, get_daily_usage

            return {
                "guard": TokenGuard.check(),
                "budget_left": get_budget_left(),
                "daily": get_daily_usage(),
            }
        except Exception:
            return {"error": "token data unavailable"}

    @staticmethod
    def _build_decisions() -> list:
        try:
            from brain.reasoning_tree import get_recent

            return get_recent(10)
        except Exception:
            return []

    @staticmethod
    def _build_full_status() -> dict:
        decisions = HQAPIHandler._build_decisions()
        baseline = HQAPIHandler._build_baseline()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": HQAPIHandler._build_health(),
            "tokens": HQAPIHandler._build_tokens(),
            "decisions": decisions[-5:],
            "decision_count": len(decisions),
            "baseline": baseline,
        }

    @staticmethod
    def _build_context_active() -> dict:
        try:
            from brain.context_manager import get_active_topic, list_topics

            return {
                "active_topic": get_active_topic(),
                "topics": list_topics(active_only=True),
                "recent_topics": list_topics(active_only=False)[-5:],
            }
        except Exception:
            return {"error": "context data unavailable"}

    @staticmethod
    def _build_persona_status() -> dict:
        try:
            from brain.persona import build_persona_context_line, build_persona_identity_block, load_persona_profile

            profile = load_persona_profile()
            return {
                "profile": profile,
                "identity_block": build_persona_identity_block(profile=profile),
                "context_line": build_persona_context_line(profile=profile),
            }
        except Exception:
            return {"error": "persona data unavailable"}

    @staticmethod
    def _build_n8n_health() -> dict:
        try:
            from brain.n8n_gate import health

            return health()
        except Exception:
            return {"error": "n8n gate unavailable"}

    @staticmethod
    def _build_dashboard_runs() -> dict:
        try:
            from brain.phase4.eval_daily import get_latest_scores
            from pathlib import Path
            scores = get_latest_scores()
            total = len(scores)
            passed = sum(1 for s in scores.values() if s.get("success"))
            return {
                "total_categories": total,
                "success_categories": passed,
                "success_rate": round(passed / total, 2) if total else 0,
                "scores": {k: {"success": v.get("success"), "error": v.get("error")}
                          for k, v in scores.items()},
            }
        except Exception:
            return {"error": "run data unavailable"}

    @staticmethod
    def _build_dashboard_skills() -> dict:
        try:
            from brain.phase4.skill_lifecycle import skill_stage_summary
            from brain.phase4.skill_advisor import get_golden_skills, find_deprecation_candidates
            summary = skill_stage_summary()
            golden = get_golden_skills()
            candidates = find_deprecation_candidates()
            return {
                "stage_summary": summary,
                "golden_skills": golden,
                "deprecation_candidates": len(candidates),
            }
        except Exception:
            return {"error": "skill data unavailable"}

    @staticmethod
    def _build_dashboard_cron() -> dict:
        try:
            from brain.phase5.cron_summary import generate_session_start_report
            report = generate_session_start_report(hours=24)
            return {
                "total_jobs": report.get("total_jobs", 0),
                "success": report.get("success", 0),
                "failed": report.get("failed", 0),
                "success_rate": report.get("success_rate", 0),
                "critical_failures": report.get("critical_failures", []),
            }
        except Exception:
            return {"error": "cron data unavailable"}

    @staticmethod
    def _build_dashboard_token_trends() -> dict:
        try:
            from brain.phase4.token_report import generate_weekly_report
            report = generate_weekly_report(hours=168)
            return {
                "total_tokens": report.get("total_tokens", 0),
                "total_entries": report.get("total_entries", 0),
                "top_expensive": report.get("top_expensive", [])[:5],
                "recommendations": report.get("recommendations", []),
            }
        except Exception:
            return {"error": "token trend data unavailable"}

    @staticmethod
    def _build_dashboard_policy() -> dict:
        try:
            from brain.phase4.autonomy_policy import self_audit
            return self_audit()
        except Exception:
            return {"error": "policy data unavailable"}

    @staticmethod
    def _build_dashboard_eval() -> dict:
        try:
            from brain.phase4.eval_daily import get_latest_scores
            scores = get_latest_scores()
            by_category = []
            for cat, data in scores.items():
                by_category.append({
                    "category": cat,
                    "success": data.get("success", False),
                    "metrics": data.get("metrics", {}),
                })
            return {"categories": by_category}
        except Exception:
            return {"error": "eval data unavailable"}

    @staticmethod
    def _build_dashboard_alarms() -> dict:
        alarms = []
        try:
            from brain.accounting import TokenGuard
            token_check = TokenGuard.check()
            if token_check.get("status") in ("flash", "stop"):
                alarms.append({
                    "level": "critical",
                    "source": "token",
                    "message": f"Token budget {token_check['status']}: {token_check.get('usage', 0):.2f} used",
                })
        except Exception:
            pass
        try:
            from brain.phase4.token_report import generate_weekly_report
            report = generate_weekly_report(hours=168)
            for rec in report.get("recommendations", []):
                alarms.append({"level": "warning", "source": "token", "message": rec})
        except Exception:
            pass
        try:
            from brain.phase5.cron_summary import check_critical_failures
            failures = check_critical_failures(hours=24)
            for f in failures:
                alarms.append({
                    "level": "critical",
                    "source": "cron",
                    "message": f"Cron job '{f.get('job_id')}' failed: {f.get('error', 'unknown')}",
                })
        except Exception:
            pass
        return {"alarms": alarms[:10], "total": len(alarms)}

    def _handle_context_close(self, data: dict) -> tuple[dict, int]:
        try:
            from brain.context_manager import close_topic, list_topics

            topic_id = data.get("topic_id")
            if data.get("close_all"):
                closed = []
                while True:
                    active = list_topics(active_only=True)
                    if not active:
                        break
                    item = close_topic(active[-1].get("id"))
                    if item is None:
                        break
                    closed.append(item)
                return {"closed": closed, "remaining": list_topics(active_only=True)}, 200
            if topic_id is None:
                topic_id = "son konu"
            closed = close_topic(topic_id)
            if closed is None:
                return {"error": "topic_not_found"}, 404
            return {"closed": closed, "remaining": list_topics(active_only=True)}, 200
        except Exception as exc:
            return {"error": str(exc)}, 500

    def _handle_n8n_write_enable(self, data: dict) -> tuple[dict, int]:
        try:
            from brain.n8n_gate import enable_write

            minutes = data.get("minutes", 60)
            reason = data.get("reason", "manual")
            health = enable_write(minutes=minutes, reason=reason, actor="hq")
            return health, 200
        except Exception as exc:
            return {"error": str(exc)}, 500

    @staticmethod
    def _build_baseline() -> dict:
        try:
            from brain.baseline import collect_baseline_snapshot

            return collect_baseline_snapshot()
        except Exception:
            return {"error": "baseline data unavailable"}

    def log_message(self, format, *args):
        return


def _memory() -> dict:
    try:
        mem = {}
        with open("/proc/meminfo", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith(("MemTotal", "MemAvailable")):
                    parts = line.split()
                    mem[parts[0].rstrip(":")] = int(parts[1]) // 1024
        return mem
    except Exception:
        return {}


def _disk() -> dict:
    try:
        st = os.statvfs("/")
        return {
            "total_gb": st.f_frsize * st.f_blocks // (1024**3),
            "free_gb": st.f_frsize * st.f_bfree // (1024**3),
        }
    except Exception:
        return {}


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False


def _systemd_active(unit: str) -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", unit],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        return result.stdout.strip() == "active"
    except Exception:
        return False


ALLOWED_COMMAND_PREFIXES = (
    "systemctl status",
    "systemctl restart hermes",
    "systemctl start hermes",
    "systemctl stop hermes",
    "journalctl -n 30 -u",
    "df -h",
    "free -m",
    "ps aux",
    "uptime",
)


def _run_allowed_command(command: str) -> tuple[dict, int]:
    if not command:
        return {"error": "Komut boş", "command": command}, 400
    if not command.startswith(ALLOWED_COMMAND_PREFIXES):
        return {"error": "Bu komuta izin verilmiyor", "command": command}, 403
    try:
        args = shlex.split(command)
    except ValueError as exc:
        return {"error": str(exc), "command": command}, 400
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=10, check=False)
        return {
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout[-1000:],
            "stderr": result.stderr[-500:],
        }, 200
    except subprocess.TimeoutExpired:
        return {"error": "Komut zaman aşımı", "command": command}, 408
    except Exception as exc:
        return {"error": str(exc), "command": command}, 500


def _handle_token_limit(data: dict) -> tuple[dict, int]:
    action = data.get("action", "")
    if action == "reset":
        return {"status": "reset_requested"}, 200
    if action == "set":
        try:
            new_limit = float(data.get("limit", 0.5))
        except (TypeError, ValueError):
            return {"error": "Geçersiz limit"}, 400
        if new_limit <= 0:
            return {"error": "Limit pozitif olmalı"}, 400
        return {"status": "limit_updated", "new_limit": new_limit}, 200
    return {"error": "Geçersiz aksiyon"}, 400


def run(port: int = 8889, host: str = "127.0.0.1"):
    server = HTTPServer((host, port), HQAPIHandler)
    print(f"HQ → http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    import sys

    run(port=int(sys.argv[1]) if len(sys.argv) > 1 else 8889)
