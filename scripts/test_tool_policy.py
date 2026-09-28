import os
import sys
import json
import time
import urllib.request

# Load prompt, tools, and guard directly from the production bot
sys.path.insert(0, "/opt/hermes")
from telegram_claude_bot import SYSTEM_PROMPT, TOOLS, should_allow_tool_call, ANTIGRAVITY_URL, MODEL

TEST_CASES = [
    {
        "id": "TEST 1",
        "prompt": "hafıza ve araç katmanın iyileştirildi. raporla",
        "expected_tool": None,
        "desc": "Raporlama isteği -> 0 Alfred çağrısı"
    },
    {
        "id": "TEST 2",
        "prompt": "Yaptığın değişiklikleri özetle.",
        "expected_tool": None,
        "desc": "Değişiklik özeti -> 0 Alfred çağrısı"
    },
    {
        "id": "TEST 3",
        "prompt": "Ekran görüntüsü al",
        "expected_tool": "take_screenshot",
        "desc": "Ekran görüntüsü -> 1 screenshot"
    },
    {
        "id": "TEST 4",
        "prompt": "Chrome da example.com u aç.",
        "expected_tool": "open_browser_url",
        "desc": "Tarayıcı açma -> 1 browser call"
    },
    {
        "id": "TEST 5",
        "prompt": "Windows Downloads klasörünü listele.",
        "expected_tool": "run_windows_command",
        "desc": "Windows dosya/komut -> 1 Windows call"
    },
    {
        "id": "TEST 6",
        "prompt": "Bu konuşmada aldığımız kararları özetle.",
        "expected_tool": None,
        "desc": "Karar özeti -> 0 Alfred çağrısı"
    },
    {
        "id": "TEST 7",
        "prompt": "Şu siteyi aç, ekran görüntüsünü al ve bana gördüklerini söyle: https://ergeneai.com",
        "expected_tool": "multi",
        "desc": "Çoklu eylem -> Gerekli olduğu kadar tool"
    }
]

print("=" * 80)
print("JEFF TOOL-USE POLICY & REGRESSION TEST SUITE")
print("=" * 80)

results = []
for tc in TEST_CASES:
    t0 = time.time()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": tc["prompt"]}
    ]
    
    body = json.dumps({
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "max_tokens": 1024,
        "temperature": 0.2
    }).encode("utf-8")
    
    req = urllib.request.Request(
        ANTIGRAVITY_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer antigravity-local"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        dt = (time.time() - t0) * 1000
        msg_obj = data["choices"][0]["message"]
        tool_calls = msg_obj.get("tool_calls") or []
        
        # Determine actual tool calls after guard
        actual_executed = []
        for tc_call in tool_calls:
            name = tc_call["function"]["name"]
            allowed, reason = should_allow_tool_call(tc["prompt"], name)
            if allowed:
                actual_executed.append(name)
            else:
                actual_executed.append(f"BLOCKED({name})")
        
        # Check pass/fail
        passed = False
        if tc["expected_tool"] is None:
            # Should have 0 executed Alfred/tools
            passed = len([x for x in actual_executed if not x.startswith("BLOCKED")]) == 0
        elif tc["expected_tool"] == "multi":
            passed = len(actual_executed) >= 1
        else:
            passed = tc["expected_tool"] in actual_executed
            
        status_str = "✅ PASS" if passed else "❌ FAIL"
        details = f"Model Proposed: {[t['function']['name'] for t in tool_calls]} | Executed: {actual_executed}"
        print(f"[{tc['id']}] {status_str} | {tc['desc']} ({dt:.1f}ms)")
        print(f"       Prompt: \"{tc['prompt']}\"")
        print(f"       {details}")
        results.append({
            "id": tc["id"],
            "status": "PASS" if passed else "FAIL",
            "prompt": tc["prompt"],
            "model_tools": [t["function"]["name"] for t in tool_calls],
            "executed": actual_executed,
            "duration_ms": dt
        })
    except Exception as exc:
        print(f"[{tc['id']}] ❌ ERROR: {exc}")
        results.append({"id": tc["id"], "status": "ERROR", "error": str(exc)})

print("=" * 80)
passed_count = sum(1 for r in results if r["status"] == "PASS")
total_count = len(results)
print(f"SUMMARY: {passed_count}/{total_count} POLICY REGRESSION TESTS PASSED.")
print("=" * 80)

with open("/home/hermes/.hermes/scripts/policy_test_results.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
