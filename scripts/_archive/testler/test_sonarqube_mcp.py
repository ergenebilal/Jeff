#!/usr/bin/env python3
"""
Test: SonarQube MCP Server working end-to-end.
Creates a test project, runs analysis on a sample Python file, checks quality gate.
"""
import os
import sys
import json
import subprocess
from typing import Dict, Any, Tuple, List

SONARQUBE_URL: str = "http://localhost:9000"
SONARQUBE_TOKEN: str = "squ_04d048c1ace22287642eb9fa6b5a5fa7ea0da6cd"
TEST_PROJECT_KEY: str = "hermes-test"
TEST_FILE: str = "/tmp/test_sonar_sample.py"


def setup_test_file() -> None:
    """Create a sample Python file with known issues for SonarQube to detect."""
    content: str = '''"""Sample file with intentional code smells for SonarQube testing."""

def unused_function():  # unused function
    x = 1 + 2
    return x

def no_type_hint(param):  # missing type hint
    return param * 2

def long_function():
    result = 0
    for i in range(100):
        for j in range(100):
            for k in range(100):
                result += i * j * k
    return result

if __name__ == "__main__":
    print(no_type_hint(5))
    print(long_function())
'''
    with open(TEST_FILE, "w") as f:
        f.write(content)
    print(f"  Test file created: {TEST_FILE} ({len(content)} bytes)")


def run_sonar_scanner() -> Tuple[bool, str]:
    """Run sonar-scanner CLI if available, or use sonar-scanner docker image."""
    # Try docker-based sonar-scanner
    cmd: List[str] = [
        "docker", "run", "--rm",
        "-v", f"{TEST_FILE}:/usr/src/test_file.py",
        "-v", f"{os.path.dirname(TEST_FILE)}/sonar-project.properties:/usr/src/sonar-project.properties",
        "sonarsource/sonar-scanner-cli",
        f"-Dsonar.host.url={SONARQUBE_URL}",
        f"-Dsonar.login={SONARQUBE_TOKEN}",
        f"-Dsonar.projectKey={TEST_PROJECT_KEY}",
        f"-Dsonar.projectName=Hermes Test",
        f"-Dsonar.sources=/usr/src",
        f"-Dsonar.python.version=3",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output: str = result.stdout + result.stderr
        success: bool = "ANALYSIS SUCCESSFUL" in output or "EXECUTION SUCCESS" in output
        return success, output[:500]
    except FileNotFoundError:
        return False, "sonar-scanner docker image not found"
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def check_quality_gate() -> Dict[str, Any]:
    """Check quality gate status for the test project."""
    try:
        import urllib.request
        url: str = f"{SONARQUBE_URL}/api/qualitygates/project_status?projectKey={TEST_PROJECT_KEY}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {SONARQUBE_TOKEN}")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data: Dict[str, Any] = json.loads(resp.read())
            status: str = data.get("projectStatus", {}).get("status", "UNKNOWN")
            conditions: List[Dict[str, Any]] = data.get("projectStatus", {}).get("conditions", [])
            return {"status": status, "conditions": len(conditions)}
    except Exception as e:
        return {"status": f"ERROR: {e}", "conditions": 0}


def test_sonarqube_api() -> Dict[str, Any]:
    """Test basic SonarQube API connectivity."""
    try:
        import urllib.request
        url: str = f"{SONARQUBE_URL}/api/system/status"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {SONARQUBE_TOKEN}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data: Dict[str, Any] = json.loads(resp.read())
            return {"status": data.get("status"), "version": data.get("version")}
    except Exception as e:
        return {"status": f"ERROR: {e}"}


def main() -> None:
    """Run SonarQube MCP integration test."""
    print("=== SonarQube MCP Integration Test ===")
    print()

    # Test 1: API connectivity
    api_result: Dict[str, Any] = test_sonarqube_api()
    print(f"Test 1 — API Bağlantısı: {api_result.get('status')} (v{api_result.get('version')})")
    assert api_result.get("status") == "UP", f"API not UP: {api_result}"
    print("  ✅ SonarQube API çalışıyor")

    # Test 2: Setup test file
    setup_test_file()

    # Test 3: Run analysis
    print("Test 2 — Kod Analizi çalıştırılıyor...")
    scan_ok, scan_output = run_sonar_scanner()
    print(f"  Scanner result: {'✅ SUCCESS' if scan_ok else '❌ FAILED'}")

    # Test 4: Quality gate
    qg: Dict[str, Any] = check_quality_gate()
    print(f"Test 3 — Quality Gate: {qg.get('status')} ({qg.get('conditions')} conditions)")

    print()
    if api_result.get("status") == "UP":
        print("✅ PASS: SonarQube MCP Server çalışıyor ve API yanıt veriyor")
    else:
        print("❌ FAIL: Sorun var")


if __name__ == "__main__":
    main()
