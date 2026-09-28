#!/usr/bin/env python3
"""
Job 1 - Lead Fetcher v2 (no_agent mode, $0)
Uses Google Places API (New) to scrape leads from Mudanya/Bursa.
Outputs JSON array to stdout for context_from chaining.
"""
import json, os, sys, time, urllib.request, urllib.error


def get_google_key():
    key = os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    for env_path in [os.path.expanduser("~/.hermes/.env"), os.path.expanduser("~/.env")]:
        if not os.path.exists(env_path):
            continue
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GOOGLE_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    if key:
                        return key
    return None


GOOGLE_API_KEY = get_google_key()
if not GOOGLE_API_KEY:
    print("FATAL: GOOGLE_API_KEY not found", file=sys.stderr)
    sys.exit(1)

QUERIES = [
    ("Mudanya sac ekimi klinigi", "sac_ekimi"),
    ("Mudanya guzellik merkezi", "guzellik"),
    ("Mudanya dis klinigi", "klinik"),
    ("Mudanya estetik klinigi", "klinik"),
    ("Mudanya restoran", "restoran"),
    ("Bursa sac ekimi klinigi", "sac_ekimi"),
    ("Bursa guzellik salonu", "guzellik"),
    ("Bursa dis poliklinigi", "klinik"),
]


def places_search(query_text, category, max_results=15):
    url = "https://places.googleapis.com/v1/places:searchText"
    payload = json.dumps({
        "textQuery": query_text,
        "languageCode": "tr",
        "maxResultCount": max_results,
    }).encode()

    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": (
                "places.displayName,places.formattedAddress,"
                "places.internationalPhoneNumber,places.websiteUri,"
                "places.rating,places.userRatingCount,places.types"
            ),
        }
    )

    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": f"HTTP {e.code}: {body[:200]}", "query": query_text}
    except Exception as e:
        return {"error": str(e), "query": query_text}

    results = []
    for place in resp.get("places", []):
        name = place.get("displayName", {}).get("text", "")
        results.append({
            "name": name,
            "phone": place.get("internationalPhoneNumber", ""),
            "website": place.get("websiteUri", ""),
            "address": place.get("formattedAddress", ""),
            "rating": place.get("rating", 0),
            "reviews_count": place.get("userRatingCount", 0),
            "types": place.get("types", []),
            "category": category,
            "search_query": query_text,
        })

    return {"query": query_text, "results": results, "count": len(results)}


def main():
    all_leads = []
    seen = set()

    for query_text, category in QUERIES:
        print(f"[{query_text[:30]}...]", file=sys.stderr)
        result = places_search(query_text, category)

        if "error" in result:
            print(f"  FAIL: {result['error']}", file=sys.stderr)
            continue

        for item in result.get("results", []):
            name = item.get("name", "").strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            all_leads.append(item)

        count = result.get("count", 0)
        print(f"  -> {count} raw, {len(all_leads)} unique so far", file=sys.stderr)
        time.sleep(0.3)

    # Output JSON to stdout - this is what context_from captures
    print(json.dumps(all_leads, ensure_ascii=False, indent=2))

    # Stats to stderr - not captured by context_from
    print("", file=sys.stderr)
    print("=== STATS ===", file=sys.stderr)
    print(f"Total unique leads: {len(all_leads)}", file=sys.stderr)
    websites = [l for l in all_leads if l.get("website")]
    phones = [l for l in all_leads if l.get("phone")]
    print(f"With website: {len(websites)}", file=sys.stderr)
    print(f"With phone: {len(phones)}", file=sys.stderr)


if __name__ == "__main__":
    main()
