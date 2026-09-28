#!/usr/bin/env python3
"""
tool-hunt-filter.py — OpenCode ham çıktısını alır, daha önce bulunan araçlarla
karşılaştırır, sadece YENİ araçları son-buluntular.md'ye yazar.
"""
import json
import os
import re
import sys

KNOWN_FILE = os.path.expanduser("~/.hermes/data/known-tools.json")
RAW_FILE = "/home/hermes/tool-hunter/ham-buluntular.md"
OUTPUT_FILE = "/home/hermes/tool-hunter/son-buluntular.md"

# Bilinen araçları yükle
if os.path.exists(KNOWN_FILE):
    with open(KNOWN_FILE) as f:
        known_data = json.load(f)
else:
    known_data = {"tools": []}

known_urls = {t["url"].rstrip("/").lower() for t in known_data["tools"]}
known_names = {t["name"].lower() for t in known_data["tools"]}

# Ham çıktıyı oku
if not os.path.exists(RAW_FILE):
    print("NO_NEW — ham buluntu dosyasi yok")
    # Boş rapor yaz
    with open(OUTPUT_FILE, "w") as f:
        f.write("# Tool Hunter — Yeni Buluntu Yok\n\n")
        f.write("Bu turda yeni bir arac bulunamadi. Bir sonraki taramada tekrar kontrol edilecek.\n")
    sys.exit(0)

with open(RAW_FILE) as f:
    raw_content = f.read()

# GitHub repo URL'lerini bul
repo_urls = re.findall(r'https?://github\.com/[\w.-]+/[\w.-]+', raw_content)
repo_names = set()
for url in repo_urls:
    clean_url = url.rstrip("/").lower()
    parts = clean_url.rstrip("/").split("/")
    if len(parts) >= 2:
        repo_names.add(f"{parts[-2]}/{parts[-1]}")

# Yeni olanları filtrele
new_names = []
for name in sorted(repo_names):
    if name not in known_names and name not in ("headroom", "chopratejas/headroom"):
        # URL'yi bul
        matching_urls = [u for u in repo_urls if name.replace("/", "/") in u.lower()]
        url = matching_urls[0] if matching_urls else f"https://github.com/{name}"
        new_names.append({"name": name, "url": url})

# Ayrıca ham çıktıda mention edilmiş ama URL'si olmayan araçları da yakala
# (OpenCode bazen link vermeden isim yazabilir)
line_patterns = re.findall(r'(?:^|\n)[*#\-\s]*(\*\*[^*]+\*\*|\[[^\]]+\])', raw_content)
for match in line_patterns:
    name = match.strip("*[]").strip()
    if name and len(name) > 2:
        name_key = name.lower().replace(" ", "-")
        if name_key not in known_names and name_key not in ("", "headroom"):
            matching_url = [u for u in repo_urls if name.lower() in u.lower().split("/")[-1]]
            if not matching_url:
                continue  # URL'si yoksa ekleme
            entry = {"name": name_key, "url": matching_url[0]}
            if entry not in new_names and entry["name"] not in [n["name"] for n in new_names]:
                new_names.append(entry)

# Yeni bulunanları bilinenler listesine ekle
if new_names:
    for t in new_names:
        known_data["tools"].append({"name": t["name"], "url": t["url"]})
    known_data["last_updated"] = "2026-06-20"

    with open(KNOWN_FILE, "w") as f:
        json.dump(known_data, f, indent=2)

    # Raporu yaz
    with open(OUTPUT_FILE, "w") as f:
        f.write("# Tool Hunter — Yeni Bulunan Araçlar\n\n")
        f.write(f"**Tarih:** $(date)\n\n")
        f.write(f"**Bu turda {len(new_names)} yeni araç bulundu.**\n\n")
        for t in new_names:
            f.write(f"- [{t['name']}]({t['url']})\n")
        f.write("\n---\n")
        f.write(f"*Bilinen toplam araç: {len(known_data['tools'])}*\n")

    for t in new_names:
        print(f"NEW: {t['name']} — {t['url']}")
    print(f"Toplam {len(new_names)} yeni arac bilinenler listesine eklendi.")
else:
    # Yeni bir şey yok
    with open(OUTPUT_FILE, "w") as f:
        f.write("# Tool Hunter — Yeni Buluntu Yok\n\n")
        f.write("Bu turda daha once gorulmemis yeni bir arac bulunamadi.\n")
        f.write(f"Bilinen toplam arac sayisi: {len(known_data['tools'])}\n")

    print("NO_NEW — bu turda yeni arac bulunamadi.")
