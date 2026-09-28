#!/usr/bin/env python3
"""
CyberGene Level 5: FAZ 2 Test Suite (Closed-Loop Autonomous Self-Healing)
Verifies Dewey + Aider self-healing capabilities end-to-end.
"""

import os
import sys
import json
import time
import subprocess
from self_healing_engine import SelfHealingEngine

def test_bridge_connectivity(engine: SelfHealingEngine):
    print("\n--- [TEST 1/3] Aider Bridge & Health Connectivity ---")
    health = engine._get("/health")
    print("Bridge Health:", json.dumps(health, indent=2))
    assert health.get("status") == "ok", "Bridge health status is not ok"
    assert health.get("aider_ready") is True, "Aider is not ready on bridge"
    print("[PASS] Test 1: Bridge is healthy and Aider engine is ready.")
    return True

def test_syntax_validation(engine: SelfHealingEngine):
    print("\n--- [TEST 2/3] AST & Syntax Pre-Flight Validation ---")
    test_dir = "/home/hermes/jeff2/self_healing_sandbox"
    os.makedirs(test_dir, exist_ok=True)
    
    # 1. Valid snippet
    valid_file = os.path.join(test_dir, "test_valid.py")
    with open(valid_file, "w") as f:
        f.write("def add(a, b):\n    return a + b\n")
    ok, msg = engine.validate_file_syntax(valid_file)
    print("Valid file check:", ok, msg)
    assert ok is True

    # 2. Corrupted snippet
    broken_file = os.path.join(test_dir, "test_broken.py")
    with open(broken_file, "w") as f:
        f.write("def broken(x\n    retrun x * 2\n")
    ok, msg = engine.validate_file_syntax(broken_file)
    print("Broken file check:", ok, msg)
    assert ok is False
    print("[PASS] Test 2: AST validator correctly catches valid and broken files.")
    return True

def test_end_to_end_self_healing(engine: SelfHealingEngine):
    print("\n--- [TEST 3/3] End-to-End Closed Loop Self-Healing ---")
    sandbox_dir = "/home/hermes/jeff2/self_healing_sandbox"
    os.makedirs(sandbox_dir, exist_ok=True)
    target_file = os.path.join(sandbox_dir, "cyber_worker_service.py")
    
    # Intentionally corrupt target file
    corrupt_code = (
        "# CyberWorker Service - Injected Fault\n"
        "import sys\n\n"
        "def process_payload(data: dict):\n"
        "    # Intentional bug: 'retrun' typo instead of 'return'\n"
        "    retrun {'status': 'processed', 'data': data}\n"
    )
    with open(target_file, "w") as f:
        f.write(corrupt_code)

    print(f"[*] Injected syntax corruption into: {target_file}")
    is_valid_before, err_msg = engine.validate_file_syntax(target_file)
    print(f"[*] Pre-repair validation result: valid={is_valid_before}, err={err_msg}")
    assert is_valid_before is False, "Target file should be invalid initially"

    print("[*] Dispatching autonomous self-healing request to Dewey & Aider Bridge...")
    start_t = time.time()
    repair_result = engine.auto_repair_file(
        target_file,
        error_description="Fix syntax error: replace invalid keyword 'retrun' with 'return' in cyber_worker_service.py",
        timeout_sec=120
    )
    duration = round(time.time() - start_t, 2)
    print(f"[*] Self-healing cycle finished in {duration}s. Result:\n", json.dumps(repair_result, indent=2))

    assert repair_result.get("ok") is True, f"Repair failed: {repair_result}"
    assert repair_result.get("status") == "HEALED_AND_VERIFIED", "Status is not HEALED_AND_VERIFIED"

    # Verify execution of the healed file
    with open(target_file, "r") as f:
        healed_code = f.read()
    print("[*] Healed Code Content:\n" + healed_code.strip())

    # Execute the healed code in Python to guarantee runtime correctness
    exec_res = subprocess.run(
        [sys.executable, "-c", f"import sys; sys.path.insert(0, '{sandbox_dir}'); import cyber_worker_service; print(cyber_worker_service.process_payload({{'test': 123}}))"],
        capture_output=True,
        text=True
    )
    print("[*] Runtime execution output:", exec_res.stdout.strip())
    assert exec_res.returncode == 0, f"Runtime execution failed: {exec_res.stderr}"
    assert "processed" in exec_res.stdout, "Runtime logic returned unexpected output"

    print("[PASS] Test 3: Autonomous self-healing repaired code, passed AST validation, and executed flawlessly!")
    return True

def main():
    print("=" * 70)
    print("   CYBERGENE LEVEL 5 : FAZ 2 (SELF-HEALING) TEST PROTOKOLU")
    print("=" * 70)
    engine = SelfHealingEngine()
    t1 = test_bridge_connectivity(engine)
    t2 = test_syntax_validation(engine)
    t3 = test_end_to_end_self_healing(engine)
    print("=" * 70)
    if t1 and t2 and t3:
        print(">>> FAZ 2 SONUC: %100 BASARILI - OTONOM ONARIM KANITLANDI <<<")
    else:
        print(">>> FAZ 2 SONUC: BASARISIZ <<<")
    print("=" * 70)

if __name__ == "__main__":
    main()
