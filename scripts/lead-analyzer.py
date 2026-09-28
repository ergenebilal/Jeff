#!/usr/bin/env python3
"""
Job 2 - Lead Analyzer (no_agent mode, $0)
Reads lead JSON from stdin (context_from), calls Crawl4AI for website analysis.
Outputs enriched JSON to stdout.
"""
import json, os, sys, urllib.request, urllib.error


CRAWL4AI_URL="http://localhost:11235"
CRAWL4AI_TOKEN=None


def load_token():
    global CRAWL4AI_TOKEN
    token = os.environ.get("CRAWL4AI_API_TOKEN")
    if token:
        CRAWL4AI_TOKEN = token
        return True
    for env_path in [os.path.expanduser("~/.hermes/.env"), os.path.expanduser("~/.env")]:
        if not os.path.exists(env_path):
            continue
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                target = "CRAWL4AI_API_TOKEN="
                if line.startswith(target):
                    CRAWL4AI_TOKEN = line.split("=", 1)[1].strip()
                    return True
    return False


if not load_token():
    print("WARNING: Crawl4AI API token not found", file=sys.stderr)
SOCIAL_DOMAINS = ["instagram.com", "facebook.com", "twitter.com", "x.com", 
                  "linkedin.com", "youtube.com", "tiktok.com", "youtu.be"]

def analyze_website(url):
    """Call Crawl4AI to analyze a website. Returns summary."""
    if not url:
        return {"url": url, "status": "no_url", "error": None}

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Check if it's a social media link
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    for social in SOCIAL_DOMAINS:
        if social in domain:
            return {"url": url, "status": "social_media", "error": None, "domain": domain}

    headers = {"Content-Type": "application/json"}
    if CRAWL4AI_TOKEN:
        headers["Authorization"] = "Bearer " + CRAWL4AI_TOKEN

    try:
        payload = json.dumps({
            "urls": [url],
            "priority": 10,
            "max_pages": 1,
        }).encode()

        req = urllib.request.Request(
            CRAWL4AI_URL + "/crawl",
            data=payload,
            method="POST",
            headers=headers,
        )

        resp = json.loads(urllib.request.urlopen(req, timeout=45).read())

        results = resp.get("results", [])
        if results and results[0].get("success"):
            r0 = results[0]
            md = r0.get("markdown", "") or ""
            return {
                "url": url,
                "status": "ok",
                "has_content": len(md) > 100,
                "content_length": len(md),
                "title": r0.get("title", ""),
            }
        else:
            err = results[0].get("error_message", "") if results else "no results"
            return {"url": url, "status": "error", "error": str(err)}

    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        return {"url": url, "status": "error", "error": "HTTP " + str(e.code) + ": " + body}
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e)}


def score_website(analysis):
    if analysis.get("status") != "ok":
        return 0
    if not analysis.get("has_content"):
        return 1
    length = analysis.get("content_length", 0)
    if length > 5000:
        return 5
    elif length > 2000:
        return 4
    elif length > 500:
        return 3
    elif length > 100:
        return 2
    return 1


def main():
    try:
        leads = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(json.dumps({"error": "Invalid JSON input: " + str(e)}))
        sys.exit(1)

    if not isinstance(leads, list):
        leads = [leads]

    print("Analyzing " + str(len(leads)) + " leads...", file=sys.stderr)

    validated_leads = []
    for lead in leads:
        website = lead.get("website", "")
        if website:
            print("  Crawling: " + lead["name"][:30] + " -> " + website[:50], file=sys.stderr)
            analysis = analyze_website(website)
            lead["website_score"] = score_website(analysis)
            lead["website_analysis"] = analysis
        else:
            lead["website_score"] = 0
            lead["website_analysis"] = {"status": "no_website"}
        validated_leads.append(lead)

    print(json.dumps(validated_leads, ensure_ascii=False, indent=2))

    print("", file=sys.stderr)
    print("=== ANALYSIS STATS ===", file=sys.stderr)
    with_site = sum(1 for l in validated_leads if l.get("website"))
    scored = sum(1 for l in validated_leads if l.get("website_score", 0) > 0)
    print("Leads with website: " + str(with_site), file=sys.stderr)
    print("Websites analyzed: " + str(scored), file=sys.stderr)
    low_score = [l for l in validated_leads if l.get("website_score", 0) <= 1]
    print("High opportunity (score 0-1): " + str(len(low_score)), file=sys.stderr)


if __name__ == "__main__":
    main()
