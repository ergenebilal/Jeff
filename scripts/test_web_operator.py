#!/usr/bin/env python3
"""
Comprehensive Web Operator & Regression Test Suite
Executes from Linux -> Windows Alfred over Tailscale.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, "/home/hermes/.hermes/scripts")
import alfred_tool as alfred

RESULTS = {}

def report(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    RESULTS[name] = passed
    print(f"[{status}] {name}: {detail}")

print("=" * 65)
print("ALFRED WEB OPERATOR VERIFICATION TEST SUITE")
print("=" * 65)

# -------------------------------------------------------------
# Test A: Browser Açma (https://example.com aç, başarılı sonucu doğrula)
# -------------------------------------------------------------
try:
    res = alfred.browser_open("https://example.com")
    ok = res.get("ok") is True and res.get("result", {}).get("opened") is True
    report("A_browser_open", ok, f"URL: {res.get('result', {}).get('url')}, Title: {res.get('result', {}).get('page_title')}")
except Exception as e:
    report("A_browser_open", False, str(e))

# -------------------------------------------------------------
# Test B: Browser read text (sayfa başlığını/metnini gerçekten oku)
# -------------------------------------------------------------
try:
    res = alfred.browser_read(mode="text", selector="h1")
    text = res.get("result", {}).get("text", "").strip()
    ok = res.get("ok") is True and "Example Domain" in text
    report("B_browser_read_text", ok, f"Read text: '{text}'")
except Exception as e:
    report("B_browser_read_text", False, str(e))

# -------------------------------------------------------------
# Test C: Browser read links (sayfadaki linkleri gerçekten al)
# -------------------------------------------------------------
try:
    res = alfred.browser_read(mode="links")
    links = res.get("result", {}).get("links", [])
    ok = res.get("ok") is True and len(links) >= 1 and any("iana.org" in l.get("href", "") or "example" in l.get("href", "") for l in links)
    report("C_browser_read_links", ok, f"Total links: {len(links)}, First: {links[0] if links else 'None'}")
except Exception as e:
    report("C_browser_read_links", False, str(e))

# -------------------------------------------------------------
# Test D: Browser read find (sayfada bilinen bir metni gerçekten bul)
# -------------------------------------------------------------
try:
    res = alfred.browser_read(mode="find", query="Example")
    count = res.get("result", {}).get("count", 0)
    found = res.get("result", {}).get("found", [])
    ok = res.get("ok") is True and count >= 1
    report("D_browser_read_find", ok, f"Found occurrences: {count}")
except Exception as e:
    report("D_browser_read_find", False, str(e))

# -------------------------------------------------------------
# Test E: Browser act scroll (sayfayı gerçekten scroll et)
# -------------------------------------------------------------
try:
    res = alfred.browser_act(action="scroll", value=200)
    action_done = res.get("result", {}).get("action_done")
    ok = res.get("ok") is True and action_done == "scroll"
    report("E_browser_act_scroll", ok, f"Action done: {action_done}, URL: {res.get('result', {}).get('current_url')}")
except Exception as e:
    report("E_browser_act_scroll", False, str(e))

# -------------------------------------------------------------
# Test F: Browser act click (güvenli ve geri döndürülebilir bir linki tıkla)
# -------------------------------------------------------------
try:
    # Click link on example.com ("a")
    res = alfred.browser_act(action="click", target="a", wait_ms=1000)
    curr_url = res.get("result", {}).get("current_url", "")
    ok = res.get("ok") is True and ("iana.org" in curr_url or "example" in curr_url)
    report("F_browser_act_click", ok, f"Navigated to: {curr_url}, Title: {res.get('result', {}).get('page_title')}")
    # Navigate back to example.com for cleanliness
    alfred.browser_act(action="navigate", target="https://example.com")
except Exception as e:
    report("F_browser_act_click", False, str(e))

# -------------------------------------------------------------
# Test G: Browser session (state oku, tab bilgisini doğrula, yeni tab aç, korunumu doğrula)
# -------------------------------------------------------------
try:
    # 1. State / status
    s1 = alfred.browser_session(action="status")
    s1_open = s1.get("result", {}).get("browser_open")
    s1_count = s1.get("result", {}).get("tab_count", 0)
    
    # 2. Open new tab
    s2 = alfred.browser_session(action="new_tab", url="https://example.com")
    s2_count = s2.get("result", {}).get("tab_count", 0)
    
    # 3. Check status again to verify persistence across calls
    s3 = alfred.browser_session(action="status")
    s3_count = s3.get("result", {}).get("tab_count", 0)

    # Close the extra tab
    alfred.browser_act(action="close_tab")
    
    ok = s1.get("ok") and s2.get("ok") and s3.get("ok") and s1_open is True and s2_count > s1_count and s3_count == s2_count
    report("G_browser_session", ok, f"Initial tabs: {s1_count}, After new_tab: {s2_count}, Persistent: {s3_count}")
except Exception as e:
    report("G_browser_session", False, str(e))

# -------------------------------------------------------------
# Test H: Screenshot (browser screenshot üret, boş/siyah olmadığını doğrula)
# -------------------------------------------------------------
try:
    ss_path = "/tmp/test_browser_shot.png"
    if os.path.exists(ss_path):
        os.remove(ss_path)
    res = alfred.browser_read(mode="screenshot", save_as=ss_path)
    ok_res = res.get("ok") is True
    file_exists = os.path.exists(ss_path)
    file_size = os.path.getsize(ss_path) if file_exists else 0
    
    # Verify valid PNG header
    is_png = False
    if file_exists and file_size > 1024:
        with open(ss_path, "rb") as f:
            header = f.read(8)
            is_png = (header == b"\x89PNG\r\n\x1a\n")

    ok = ok_res and file_exists and file_size > 10000 and is_png
    report("H_screenshot", ok, f"File: {ss_path}, Size: {file_size} bytes, Valid PNG: {is_png}")
except Exception as e:
    report("H_screenshot", False, str(e))

# -------------------------------------------------------------
# Test I: Multi-step pipeline (Aynı browser session üzerinde: open -> read -> act -> read -> screenshot)
# -------------------------------------------------------------
try:
    # 1. Open / navigate
    step1 = alfred.browser_open("https://example.com")
    t1_ok = step1.get("ok") is True
    
    # 2. Read
    step2 = alfred.browser_read(mode="text", selector="h1")
    t2_text = step2.get("result", {}).get("text", "").strip()
    t2_ok = step2.get("ok") is True and "Example Domain" in t2_text
    
    # 3. Act (click 'a')
    step3 = alfred.browser_act(action="click", target="a", wait_ms=1000)
    t3_url = step3.get("result", {}).get("current_url", "")
    t3_ok = step3.get("ok") is True and ("iana.org" in t3_url or "example" in t3_url)
    
    # 4. Read (verify new page content)
    step4 = alfred.browser_read(mode="text", selector="body")
    t4_text = step4.get("result", {}).get("text", "")
    t4_ok = step4.get("ok") is True and len(t4_text) > 50
    
    # 5. Screenshot
    ms_ss_path = "/tmp/test_multistep.png"
    step5 = alfred.browser_read(mode="screenshot", save_as=ms_ss_path)
    t5_ok = step5.get("ok") is True and os.path.exists(ms_ss_path) and os.path.getsize(ms_ss_path) > 10000

    ok = t1_ok and t2_ok and t3_ok and t4_ok and t5_ok
    report("I_multi_step", ok, f"Steps: open={t1_ok}, read1={t2_ok}, act={t3_ok}, read2={t4_ok}, ss={t5_ok}")
except Exception as e:
    report("I_multi_step", False, str(e))

# -------------------------------------------------------------
# Test J: Regression Suite (ping, health, screenshot, browser, shell, read, write, ls, wa)
# -------------------------------------------------------------
try:
    reg_results = {}
    
    # 1. ping
    r_ping = alfred.ping("test_regression")
    reg_results["ping"] = r_ping.get("ok") is True
    
    # 2. health
    r_health = alfred.get_health()
    reg_results["health"] = r_health.get("ok") is True or r_health.get("status") == "healthy"
    
    # 3. screenshot (desktop)
    d_ss_path = "/tmp/test_desktop_shot.png"
    r_dss = alfred.screenshot(save_as=d_ss_path)
    reg_results["screenshot"] = r_dss.get("ok") is True and os.path.exists(d_ss_path) and os.path.getsize(d_ss_path) > 10000
    
    # 4. browser
    r_br = alfred.browser_open("https://example.com")
    reg_results["browser"] = r_br.get("ok") is True
    
    # 5. shell
    r_sh = alfred.shell("Get-Date")
    reg_results["shell"] = r_sh.get("ok") is True and r_sh.get("result", {}).get("exit_code") == 0
    
    # 6. write
    test_file = r"C:\Users\lenovo\AppData\Local\Temp\jeff_webop_reg.txt"
    r_wr = alfred.file_write(test_file, "regression_check_2026")
    reg_results["write"] = r_wr.get("ok") is True
    
    # 7. read
    r_rd = alfred.file_read(test_file)
    reg_results["read"] = r_rd.get("ok") is True and "regression_check_2026" in r_rd.get("result", {}).get("content", "")
    
    # 8. ls
    r_ls = alfred.file_list(r"C:\Users\lenovo\AppData\Local\Temp")
    reg_results["ls"] = r_ls.get("ok") is True
    
    # 9. wa
    r_wa = alfred.whatsapp_draft("+905551234567", "test draft")
    reg_results["wa"] = r_wa.get("ok") is True
    
    ok = all(reg_results.values())
    failed = [k for k, v in reg_results.items() if not v]
    report("J_regression", ok, f"Passed {len(reg_results)-len(failed)}/{len(reg_results)} (Failed: {failed if failed else 'None'})")
except Exception as e:
    report("J_regression", False, str(e))

print("=" * 65)
all_pass = all(RESULTS.values())
print(f"OVERALL RESULT: {'PASS' if all_pass else 'FAIL'} ({sum(RESULTS.values())}/{len(RESULTS)} passed)")
print("=" * 65)

sys.exit(0 if all_pass else 1)
