#!/usr/bin/env python3
"""Test pipeline: fetch a few leads, then analyze with Crawl4AI."""
import json, subprocess, sys

# Step 1: Fetch small set
env = {"APIFY_TOKEN": "", "CRAWL4AI_API_TOKEN": "", "GOOGLE_API_KEY": ""}
# Read env
with open("/home/hermes/.hermes/.env") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v

# Override QUERIES via env
test_env = env.copy()
test_env["TEST_QUERIES"] = "1"  # signal to use first query only

# Run lead fetcher
import urllib.request

# Test Google Places API with just 1 query
url = "https://places.googleapis.com/v1/places:searchText"
payload = json.dumps({
    "textQuery": "Mudanya saç ekimi kliniği",
    "languageCode": "tr",
    "maxResultCount": 5,
}).encode()

req = urllib.request.Request(
    url, data=payload, method="POST",
    headers={
        "Content-Type": "application/json",
        "X-Goog-Api-Key": env.get("GOOGLE_API_KEY", ""),
        "X-Goog-FieldMask": (
            "places.displayName,places.formattedAddress,"
            "places.internationalPhoneNumber,places.websiteUri,"
            "places.rating,places.userRatingCount"
        ),
    }
)

resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
leads = []
for place in resp.get("places", []):
    name = place.get("displayName", {}).get("text", "")
    leads.append({
        "name": name,
        "phone": place.get("internationalPhoneNumber", ""),
        "website": place.get("websiteUri", ""),
        "address": place.get("formattedAddress", ""),
        "rating": place.get("rating", 0),
    })

print(f"\n=== FETCHED {len(leads)} LEADS ===")
for l in leads:
    print(f"  {l['name']} | {l.get('website','no site')[:40]}")

# Step 2: Analyze with Crawl4AI
crawl_token = env.get("CRAWL4AI_API_TOKEN", "")
headers = {"Content-Type": "application/json"}
if crawl_token:
    headers["Authorization"] = "Bearer " + crawl_token

print(f"\n=== ANALYZING WEBSITES ===")
for lead in leads:
    website = lead.get("website", "")
    if not website:
        print(f"  {lead['name'][:30]}: no website")
        lead["website_score"] = 0
        continue
    
    if not website.startswith(("http://", "https://")):
        website = "https://" + website
    
    try:
        crawl_payload = json.dumps({
            "urls": website,
            "priority": 10,
            "max_pages": 1,
        }).encode()
        
        crawl_req = urllib.request.Request(
            "http://localhost:11235/crawl",
            data=crawl_payload,
            method="POST",
            headers=headers,
        )
        
        crawl_resp = json.loads(urllib.request.urlopen(crawl_req, timeout=30).read())
        result_id = crawl_resp.get("result_id", crawl_resp.get("id"))
        
        if result_id:
            import time
            time.sleep(1)
            result_req = urllib.request.Request(
                "http://localhost:11235/result/" + str(result_id),
                headers={"Content-Type": "application/json"},
            )
            content = json.loads(urllib.request.urlopen(result_req, timeout=15).read())
            md = content.get("markdown", "") or content.get("content", "") or ""
            lead["website_score"] = 5 if len(md) > 5000 else 4 if len(md) > 2000 else 3 if len(md) > 500 else 2 if len(md) > 100 else 1
            print(f"  {lead['name'][:30]}: score={lead['website_score']} ({len(md)} chars)")
        else:
            print(f"  {lead['name'][:30]}: queued (no result_id)")
            lead["website_score"] = 0
            
    except Exception as e:
        print(f"  {lead['name'][:30]}: ERROR {str(e)[:80]}")
        lead["website_score"] = 0

print(f"\n=== FINAL ===")
print(json.dumps(leads, ensure_ascii=False, indent=2))
