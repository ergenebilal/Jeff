#!/usr/bin/env python3
"""
Test: System readiness for SonarQube MCP Server.
Checks RAM, swap, disk space, and Docker availability.
"""
import os
import sys
import json
import subprocess
from typing import Dict, Any, List, Tuple


REQUIRED_RAM_MB: int = 2048  # SonarQube minimum
REQUIRED_DISK_GB: int = 10
RECOMMENDED_SWAP_GB: int = 8


def run_cmd(cmd: List[str]) -> Tuple[int, str]:
    """Run shell command, return (exit_code, stdout)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout.strip()
    except FileNotFoundError:
        return -1, f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -2, "Timeout"
    except Exception as e:
        return -3, str(e)


def test_ram() -> Dict[str, Any]:
    """Check available RAM."""
    rc, out = run_cmd(["free", "-m"])
    if rc != 0:
        return {"status": "FAIL", "detail": f"free command error: {out}"}

    for line in out.split("\n"):
        if line.startswith("Mem:"):
            parts = line.split()
            total = int(parts[1])
            avail = int(parts[6])
            result = {
                "total_mb": total,
                "available_mb": avail,
                "sufficient": avail >= REQUIRED_RAM_MB,
            }
            print(f"  RAM: {total}MB total, {avail}MB available (need {REQUIRED_RAM_MB}MB)")
            return result

    return {"status": "FAIL", "detail": "Could not parse free output"}


def test_swap() -> Dict[str, Any]:
    """Check swap size and usage."""
    rc, out = run_cmd(["swapon", "--show", "--bytes"])
    if rc != 0 or not out:
        return {"status": "FAIL", "detail": "No swap or swapon error"}

    lines = out.strip().split("\n")
    if len(lines) < 2:
        return {"status": "FAIL", "detail": "No swap entries"}

    header = lines[0].split()
    data = lines[1].split()
    size_bytes = int(data[header.index("SIZE")])
    used_bytes = int(data[header.index("USED")])
    size_gb = size_bytes / (1024**3)
    used_gb = used_bytes / (1024**3)
    path = data[0]

    result = {
        "path": path,
        "size_gb": round(size_gb, 1),
        "used_gb": round(used_gb, 1),
        "usage_pct": round((used_bytes / size_bytes) * 100, 1) if size_bytes > 0 else 0,
    }
    print(f"  Swap: {result['size_gb']}G total, {result['used_gb']}G used ({result['usage_pct']}%)")
    return result


def test_disk() -> Dict[str, Any]:
    """Check disk space on root."""
    stat = os.statvfs("/")
    free_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)
    result = {"free_gb": round(free_gb, 1), "sufficient": free_gb >= REQUIRED_DISK_GB}
    print(f"  Disk: {result['free_gb']}G free (need {REQUIRED_DISK_GB}G)")
    return result


def test_docker() -> Dict[str, Any]:
    """Check Docker is running."""
    rc, out = run_cmd(["docker", "info", "--format", "{{.ServerVersion}}"])
    if rc != 0:
        return {"status": "FAIL", "detail": f"Docker not available: {out}"}
    result = {"docker_version": out, "running": True}
    print(f"  Docker: v{out}")
    return result


def main() -> None:
    """Run all readiness checks."""
    print("=== SonarQube MCP — System Readiness Test ===")
    print()

    checks = {
        "ram": test_ram(),
        "disk": test_disk(),
        "docker": test_docker(),
    }
    swap_result = test_swap()

    print()
    all_pass = all(
        c.get("status") != "FAIL" and c.get("sufficient", True)
        for c in checks.values()
    )

    # Swap check: should have >= 4G and room to grow
    swap_ok = swap_result.get("size_gb", 0) >= 4
    if not swap_ok:
        print("  ⚠️  Swap < 4G, should expand")
        all_pass = False

    if all_pass and swap_ok:
        print("\n✅ PASS: System ready for SonarQube deployment")
    else:
        print("\n⚠️  Some checks failed — see above")


if __name__ == "__main__":
    main()
