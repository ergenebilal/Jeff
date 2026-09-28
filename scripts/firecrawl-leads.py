#!/usr/bin/env python3
"""
Firecrawl Lead Generator — GitHub'da AI agent/automation ile ilgili yeni repoları tarar
Çalışma: Her 6 saat (cron)
Output: /tmp/leads_today.json
"""
import json
import os
import subprocess
import sys
import urllib.parse
from datetime import datetime
from urllib.request import Request, urlopen

GITHUB_API = "https://api.github.com"
FIREPOPS_FILE = "/tmp/leads_today.json"

def search_github_trending():
    """GitHub'da son 24 saatte yıldız alan AI agent repolarını bul"""
    # Son 1 haftada oluşturulmuş, AI agent konulu repolar
    queries = [
        "topic:ai-agent created:>2026-06-01 sort:stars",
        "topic:automation created:>2026-06-01 sort:stars",
        "topic:n8n created:>2026-06-01 sort:stars",
        "topic:autonomous-agent created:>2026-06-01 sort:stars",
        "hermes+agent+setup created:>2026-06-01 sort:stars",
        "ai+agent+framework created:>2026-06-01 sort:stars",
    ]
    
    all_repos = []
    for query in queries:
        try:
            encoded = urllib.parse.quote(query, safe=':+>')
            url = f"{GITHUB_API}/search/repositories?q={encoded}&per_page=5"
            req = Request(url, headers={"Accept": "application/vnd.github.v3+json"})
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                for item in data.get("items", []):
                    all_repos.append({
                        "name": item["full_name"],
                        "url": item["html_url"],
                        "stars": item["stargazers_count"],
                        "description": item.get("description", ""),
                        "language": item.get("language", ""),
                        "created": item["created_at"],
                        "owner": item["owner"]["login"],
                    })
        except Exception as e:
            print(f"  Hata ({query}): {e}")
    
    # Benzersiz repo
    seen = set()
    unique = []
    for r in all_repos:
        if r["name"] not in seen:
            seen.add(r["name"])
            unique.append(r)
    
    return unique

def classify_lead(repo):
    """Bir reponun bizim ürünlerimizle ilgisini değerlendir"""
    desc = (repo.get("description") or "").lower()
    name = repo["name"].lower()
    
    # İlgi skoru
    score = 0
    keywords = [
        "agent", "automation", "n8n", "workflow", "hermes", "ai",
        "autonomous", "bot", "pipeline", "monitoring", "no-code"
    ]
    match_count = sum(1 for k in keywords if k in desc or k in name)
    score += match_count * 10
    
    # Yıldız bonusu
    stars = repo.get("stars", 0)
    if stars >= 100:
        score += 20
    elif stars >= 50:
        score += 10
    elif stars >= 10:
        score += 5
    
    # Dil bonusu
    lang = repo.get("language", "")
    if lang in ["Python", "TypeScript", "JavaScript"]:
        score += 5
    elif lang == "Go":
        score += 3
    
    return min(score, 100)

def generate_leads():
    """Lead listesi oluştur"""
    print("🔍 GitHub'da AI agent/automation repoları taranıyor...")
    repos = search_github_trending()
    print(f"  {len(repos)} repo bulundu")
    
    leads = []
    for repo in repos:
        score = classify_lead(repo)
        if score >= 15:  # Eşik değer
            leads.append({
                "repo": repo["name"],
                "url": repo["url"],
                "stars": repo["stars"],
                "description": repo["description"],
                "score": score,
                "timestamp": datetime.now().isoformat(),
            })
    
    # Skora göre sırala
    leads.sort(key=lambda x: x["score"], reverse=True)
    
    # Kaydet
    with open(FIREPOPS_FILE, "w") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_repos": len(repos),
            "total_leads": len(leads),
            "leads": leads,
        }, f, indent=2)
    
    print(f"  {len(leads)} lead bulundu (puan >= 15)")
    print(f"  Kaydedildi: {FIREPOPS_FILE}")
    
    # Rapor
    if leads:
        print("\n🏆 EN İYİ 5 LEAD:")
        for l in leads[:5]:
            print(f"  {l['score']:3d}p | {l['repo']} ({l['stars']}⭐)")
            print(f"       {l['url']}")
    
    return leads

def main():
    print("=" * 50)
    print("🔥 FIRECRAWL LEAD GENERATOR")
    print(f"⏰ {datetime.now().strftime('%d %B %Y %H:%M')}")
    print("=" * 50)
    
    leads = generate_leads()
    
    print(f"\n✅ {len(leads)} lead / {len(set(l['repo'] for l in leads))} benzersiz repo")
    print("(Elle inceleme için: /tmp/leads_today.json)")

if __name__ == "__main__":
    main()
