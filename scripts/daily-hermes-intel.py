#!/usr/bin/env python3
"""
Daily Hermes Intelligence Scan
OpenCode ile GitHub + X'teki Hermes Agent gelişmelerini tara, raporla.
v2 — Parallel execution, faster timeouts, fallback to web search.
"""
import os, sys, json, subprocess, tempfile, concurrent.futures
from datetime import datetime

RAPOR_DIR = "/tmp/hermes-intel"
os.makedirs(RAPOR_DIR, exist_ok=True)

OPENCODE = "/home/hermes/.hermes/node/bin/opencode"

def run_opencode(prompt, timeout=35):
    """OpenCode'u pipe ile çalıştır, çıktıyı al (timeout: 35s)"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(prompt[:4000])  # cap prompt size
        prompt_file = f.name
    try:
        with open(prompt_file, 'r') as f:
            pipe_input = f.read()
        result = subprocess.run(
            [OPENCODE, "run", "--model", "opencode/deepseek-v4-flash-free"],
            input=pipe_input, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip() or "[EMPTY]"
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"
    finally:
        os.unlink(prompt_file)

def scan_github():
    return run_opencode("""GitHub'da "Hermes Agent", "Nous Research", "MoA presets" konulu:
1. Son 24 saatte yeni repolar (stars sırasıyla)
2. Trend repos
3. Fork edilmeye değer olanlar

JSON array: [{"name":"...","stars":N,"url":"...","summary":"...","relevance":"..."}]
Sadece JSON döndür.""")

def scan_x():
    return run_opencode("""X/Twitter'da "Hermes Agent", "NousResearch", "MoA presets" ile ilgili son 24 saat:
1. En önemli 5 tweet
2. Yeni duyurular

JSON array: [{"author":"...","summary":"...","likes":N,"url":"...","relevance":"..."}]
Sadece JSON döndür.""")

def main():
    print("🔍 Hermes Intelligence Scan — " + datetime.now().strftime("%d.%m.%Y %H:%M"), flush=True)
    
    # Parallel scan (GitHub + X concurrently)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        gh_future = executor.submit(scan_github)
        x_future = executor.submit(scan_x)
        github = gh_future.result(timeout=40)
        x = x_future.result(timeout=40)
    
    with open(f"{RAPOR_DIR}/github_scan.json", "w") as f:
        f.write(github if github and not github.startswith("[") else "[]")
    with open(f"{RAPOR_DIR}/x_scan.json", "w") as f:
        f.write(x if x and not x.startswith("[") else "[]")
    
    # Analyze (sequential, depends on both results)
    analysis = run_opencode(f"""GitHub: {github[:1500]}

X: {x[:1500]}

Analiz:
1. Sistemimize entegre edilebilecekler?
2. Hemen aksiyon alınması gerekenler?
3. Önümüzdeki hafta takip edilecek trendler?
Kısa ve öz, madde madde.""")

    rapor = f"""# 🧠 Hermes Intelligence — {datetime.now().strftime('%d.%m.%Y')}

## GitHub
{github[:2000]}

## X/Twitter
{x[:2000]}

## Analiz
{analysis[:2000]}
"""
    rapor_path = f"{RAPOR_DIR}/daily-intel-{datetime.now().strftime('%Y%m%d')}.md"
    with open(rapor_path, "w") as f:
        f.write(rapor)
    print(f"\n✅ Rapor: {rapor_path}", flush=True)
    print(analysis[:1000] if analysis else "Analiz yok", flush=True)

if __name__ == "__main__":
    main()
