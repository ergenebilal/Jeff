import os
import sys
import json
import time
import asyncio
import urllib.request

sys.path.insert(0, "/opt/hermes")
import telegram_claude_bot as bot

print("=" * 80)
print("TEST RUNNER: JEFF MULTI-TURN & ALFRED DIRECT EXECUTION VERIFICATION")
print("=" * 80)

async def simulate_turn(prompt: str, test_id: str):
    print(f"\n--- [{test_id}] PROMPT: \"{prompt}\" ---")
    messages = [
        {"role": "system", "content": bot.SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    
    max_turns = 3
    turn = 0
    all_tool_calls = []
    executed_tools = []
    
    while turn < max_turns:
        turn += 1
        t0 = time.time()
        raw_res = await bot.call_antigravity(messages)
        msg_obj = raw_res["choices"][0]["message"]
        tool_calls = msg_obj.get("tool_calls") or []
        dt = (time.time() - t0) * 1000
        
        print(f"  [Turn {turn}] Model response in {dt:.1f}ms | Tool Calls: {[tc['function']['name'] for tc in tool_calls]}")
        
        if not tool_calls:
            final_content = msg_obj.get("content", "").strip()
            print(f"  [Turn {turn}] Final text output generated ({len(final_content)} chars)")
            print(f"  [Turn {turn}] Snippet: {final_content[:200]}...")
            return {
                "test_id": test_id,
                "turns": turn,
                "proposed_tools": all_tool_calls,
                "executed_tools": executed_tools,
                "final_content": final_content
            }
            
        all_tool_calls.extend([tc["function"]["name"] for tc in tool_calls])
        messages.append({"role": "assistant", "content": msg_obj.get("content") or "", "tool_calls": tool_calls})
        
        for tc in tool_calls:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except Exception:
                args = {}
                
            out, photo, rejected = bot.execute_tool_call(name, args, user_message=prompt)
            status_tag = "REJECTED" if rejected else "EXECUTED"
            print(f"    -> Tool: {name} | Status: {status_tag} | Out: {out[:120]}...")
            if not rejected:
                executed_tools.append(name)
            messages.append({"role": "tool", "content": out, "tool_call_id": tc["id"]})
            
    return {
        "test_id": test_id,
        "turns": turn,
        "proposed_tools": all_tool_calls,
        "executed_tools": executed_tools,
        "final_content": "Max turns reached"
    }

async def main():
    # Test A: Raporlama (0 tool)
    res_a = await simulate_turn("Hafıza ve araç katmanında yapılan son iyileştirmeleri özetle.", "TEST A")
    
    # Test B: Chrome durumu (Alfred komut veya screenshot)
    res_b = await simulate_turn("Windows bilgisayarımda şu anda Chrome'da hangi sayfanın açık olduğunu öğren ve bana söyle.", "TEST B")
    
    # Test C: Downloads klasörü (Alfred powershell/ls)
    res_c = await simulate_turn("Windows bilgisayarımda Downloads klasöründe neler var?", "TEST C")
    
    # Test D: Ekran görüntüsü (take_screenshot)
    res_d = await simulate_turn("Ekran görüntüsü al.", "TEST D")
    
    # Test E: Değişiklik raporu (0 tool)
    res_e = await simulate_turn("Şimdiye kadar yaptığımız değişiklikleri raporla.", "TEST E")
    
    # Test F: Çoklu adım (Chrome aç -> Ekran görüntüsü al)
    res_f = await simulate_turn("Chrome'u aç, example.com'a git ve sonra ekran görüntüsünü al.", "TEST F")
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED. SUMMARY TABLE:")
    print("=" * 80)
    for r in [res_a, res_b, res_c, res_d, res_e, res_f]:
        print(f"[{r['test_id']}] Turns: {r['turns']} | Proposed: {r['proposed_tools']} | Executed: {r['executed_tools']}")

asyncio.run(main())
