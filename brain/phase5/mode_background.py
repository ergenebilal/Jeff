"""Background mode: isolated session, retry policy, delivery target, resource budget."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

# Background mode limits
SOFT_LIMIT = 40_000
HARD_LIMIT = 80_000
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5

# Output directory for background jobs
OUTPUT_DIR = Path.home() / ".hermes" / "cron" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class BackgroundMode:
    """Background mode executor — cron-triggered, isolated, resource-budgeted."""

    def __init__(self, context_limit: int = SOFT_LIMIT, output_dir: Optional[Path] = None):
        self.context_limit = context_limit
        self.mode_name = "background"
        self.output_dir = output_dir or OUTPUT_DIR

    def estimate_context_fit(self, current_tokens: int) -> dict:
        """Check if current context fits within background mode limits."""
        return {
            "mode": "background",
            "current": current_tokens,
            "soft_limit": SOFT_LIMIT,
            "hard_limit": HARD_LIMIT,
            "within_soft": current_tokens <= SOFT_LIMIT,
            "within_hard": current_tokens <= HARD_LIMIT,
        }

    def run_job(self, job_id: str, task: str,
                executor: Optional[Callable] = None,
                retries: int = MAX_RETRIES) -> dict:
        """Run a background job with retry policy.

        Args:
            job_id: Unique job identifier.
            task: Task description or input.
            executor: Optional callable to execute the job.
            retries: Max number of retries on failure.

        Returns:
            Dict with job result and metadata.
        """
        attempt = 0
        last_error = None

        while attempt <= retries:
            attempt += 1
            try:
                if executor:
                    result = executor(task)
                else:
                    result = {"output": f"Background job '{job_id}' processed", "status": "ok"}

                job_result = {
                    "job_id": job_id,
                    "mode": "background",
                    "task": task,
                    "attempt": attempt,
                    "success": True,
                    "result": result,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                self._save_output(job_id, job_result)
                return job_result

            except Exception as e:
                last_error = str(e)
                if attempt <= retries:
                    time.sleep(RETRY_DELAY_SEC * attempt)  # exponential backoff
                continue

        # All retries exhausted
        failed_result = {
            "job_id": job_id,
            "mode": "background",
            "task": task,
            "attempt": attempt - 1,
            "success": False,
            "error": last_error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._save_output(job_id, failed_result)
        return failed_result

    def _save_output(self, job_id: str, result: dict):
        """Save job output to the output directory."""
        path = self.output_dir / f"{job_id}.json"
        try:
            path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def get_job_output(self, job_id: str) -> Optional[dict]:
        """Retrieve saved job output."""
        path = self.output_dir / f"{job_id}.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return None

    def list_jobs(self) -> list:
        """List all background job outputs."""
        if not self.output_dir.exists():
            return []
        jobs = []
        for f in sorted(self.output_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                jobs.append({
                    "job_id": data.get("job_id", f.stem),
                    "success": data.get("success", False),
                    "timestamp": data.get("timestamp", ""),
                })
            except (json.JSONDecodeError, OSError):
                pass
        return jobs
