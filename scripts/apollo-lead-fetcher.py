#!/usr/bin/env python3
"""Apollo.io Lead Fetcher — sektör bazlı şirket/kişi getirir.
Kullanım: python3 apollo-lead-fetcher.py "restaurant" "beauty" "dental"
Çıktı: /tmp/apollo-leads-{tarih}.json
"""
import json, sys, os, time
from urllib.request import Request, urlopen

API_KEY = "Wg8BLfIsMWwaOLI7W9wuvQ"
BASE = "https://api.apollo.io/api/v1"

def search_organizations(keyword, page=1, per_page=10):
    url = f"{BASE}/organizations/search"
    data = json.dumps({
        "page": page,
        "per_page": per_page,
        "organization_num_employees_ranges": ["1,30"],
        "q_organization_name": keyword,
        "organization_locations": ["Turkey"]
    }).encode()
    req = Request(url, data=data, method="POST",
                  headers={"Content-Type": "application/json",
                           "X-Api-Key": API_KEY})
    with urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    keywords = sys.argv[1:] if len(sys.argv) > 1 else ["restaurant", "beauty", "dental", "clinic"]
    all_results = {}
    
    for kw in keywords:
        print(f"[*] '{kw}' taranıyor...")
        try:
            result = search_organizations(kw)
            total = result.get("pagination", {}).get("total_entries", 0)
            orgs = result.get("organizations", [])
            all_results[kw] = {
                "total": total,
                "organizations": [{
                    "name": o.get("name"),
                    "website": o.get("website_url"),
                    "phone": o.get("sanitized_phone"),
                    "industry": o.get("industry"),
                    "employees": o.get("estimated_num_employees"),
                    "linkedin": o.get("linkedin_url"),
                    "city": o.get("city"),
                    "country": o.get("country")
                } for o in orgs]
            }
            print(f"  -> {total} sonuç, {len(orgs)} adet getirildi")
        except Exception as e:
            print(f"  -> HATA: {e}")
        time.sleep(0.5)  # rate limiting
    
    # JSON çıktı
    output_path = f"/tmp/apollo-leads-{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Kaydedildi: {output_path}")
    
    # Özet
    print("\n=== ÖZET ===")
    for kw, data in all_results.items():
        print(f"{kw}: {data['total']} sonuç")
        for org in data['organizations'][:3]:
            print(f"  - {org['name']} | {org.get('website','')[:30] or '-'} | {org.get('phone','') or '-'}")

if __name__ == "__main__":
    main()
