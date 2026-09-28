#!/usr/bin/env python3
"""
CyberGene Level 5: FAZ 3 Test Suite (Event-Driven State Bus - Race Free)
Validates atomic state transitions, pub/sub stream delivery, and 100 concurrent workers stress test.
"""

import os
import sys
import time
import asyncio
import tempfile
from state_bus import AsyncStateBus, EventDrivenStateBus

def test_atomic_state():
    print("\n--- [TEST 1/3] Atomic State & Versioning ---")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    bus = EventDrivenStateBus(db_path)
    # 1. Initial set
    v1 = bus.set_state("system_mode", "autonomous")
    val, ver = bus.get_state("system_mode")
    print(f"Set 1 -> val: {val}, ver: {ver}")
    assert val == "autonomous"
    assert ver == 1

    # 2. Update
    v2 = bus.set_state("system_mode", "guarded_level5")
    val, ver = bus.get_state("system_mode")
    print(f"Set 2 -> val: {val}, ver: {ver}")
    assert val == "guarded_level5"
    assert ver == 2

    # 3. Atomic increment
    c1 = bus.atomic_increment("request_counter", 1)
    c2 = bus.atomic_increment("request_counter", 5)
    print(f"Counter -> {c1}, then {c2}")
    assert c1 == 1
    assert c2 == 6
    print("[PASS] Test 1: Atomic state and versioning passed.")
    try:
        os.remove(db_path)
    except Exception:
        pass
    return True

def test_pubsub_event_stream():
    print("\n--- [TEST 2/3] Pub/Sub Event Stream Monotonicity ---")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    bus = EventDrivenStateBus(db_path)
    e1 = bus.publish_event("agent_health", {"agent": "alfred", "status": "ok"})
    e2 = bus.publish_event("agent_health", {"agent": "jeff", "status": "ok"})
    e3 = bus.publish_event("system_audit", {"audit": "baseline_verified"})

    print(f"Published event IDs: {e1}, {e2}, {e3}")
    assert e2 > e1
    assert e3 > e2

    # Poll agent_health
    events = bus.poll_events("agent_health", after_id=0)
    print(f"Polled agent_health events count: {len(events)}")
    assert len(events) == 2
    assert events[0]["payload"]["agent"] == "alfred"
    assert events[1]["payload"]["agent"] == "jeff"

    print("[PASS] Test 2: Pub/Sub event ordering and filtering passed.")
    try:
        os.remove(db_path)
    except Exception:
        pass
    return True

async def test_concurrency_stress():
    print("\n--- [TEST 3/3] 100 Concurrent Async Workers (Zero-Lock Stress Test) ---")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    bus = AsyncStateBus(db_path)
    NUM_WORKERS = 100
    errors = []

    async def worker_task(worker_id: int):
        try:
            # Atomic state counter increment
            await bus.atomic_increment("shared_stress_counter", 1)
            # Pub/sub publish
            await bus.publish_event("stress_topic", {"worker_id": worker_id, "timestamp": time.time()})
        except Exception as e:
            errors.append((worker_id, str(e)))

    start_t = time.time()
    # Launch 100 workers concurrently
    tasks = [worker_task(i) for i in range(NUM_WORKERS)]
    await asyncio.gather(*tasks)
    elapsed = round(time.time() - start_t, 3)

    final_counter, _ = await bus.get_state("shared_stress_counter")
    events = await bus.poll_events("stress_topic", limit=200)

    print(f"[*] 100 concurrent workers finished in {elapsed}s.")
    print(f"[*] Total Errors encountered: {len(errors)}")
    print(f"[*] Final Counter Value: {final_counter} (Expected: {NUM_WORKERS})")
    print(f"[*] Total Events Collected: {len(events)} (Expected: {NUM_WORKERS})")

    assert len(errors) == 0, f"Encountered errors during stress test: {errors}"
    assert int(final_counter) == NUM_WORKERS, f"Lost updates detected! Final counter: {final_counter}"
    assert len(events) == NUM_WORKERS, f"Dropped events detected! Total events: {len(events)}"

    print("[PASS] Test 3: 100 concurrent workers completed with 0 errors and 0 lost updates!")
    try:
        os.remove(db_path)
    except Exception:
        pass
    return True

async def main():
    print("=" * 70)
    print("   CYBERGENE LEVEL 5 : FAZ 3 (STATE BUS) TEST PROTOKOLU")
    print("=" * 70)
    t1 = test_atomic_state()
    t2 = test_pubsub_event_stream()
    t3 = await test_concurrency_stress()
    print("=" * 70)
    if t1 and t2 and t3:
        print(">>> FAZ 3 SONUC: %100 BASARILI - OLAY GUDUMLU OMURGA ISPATLANDI <<<")
    else:
        print(">>> FAZ 3 SONUC: BASARISIZ <<<")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
