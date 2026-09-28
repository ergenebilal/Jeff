# Automated Lead Analysis Pipeline — 19.06.2026 Implementation

## Architecture

```
Google Places API (New)
  → scrape_places_api() in scraper.py
    → results[] with name, phone, address, website, lat/lng, rating
  → add_to_crm() → leads.json
    → geocoding via Nominatim (OSM) for extra precision

analyze_all_leads() in analyzer.py
  → for each lead:
    1. check_website(url) → web_score, tech_stack, reachable
    2. analyze_lead(lead) → priority, needs[], opportunities[]
    3. generate_message(lead) → personalized outreach text
  → save to leads.json (analysis + message fields)

Frontend (index.html)
  → priority badge (🔴/🟡/⚪) on lead card
  → analysis block in detail panel
  → message with "Kopyala" button
  → priority filter dropdown
  → "Analiz" button in navbar to trigger /api/analyze
```

## Key Files

| File | Path | Purpose |
|------|------|---------|
| analyzer.py | `/home/hermes/ergeneai-dashboard/analyzer.py` | Web analysis, need detection, message generation |
| scraper.py | `/home/hermes/ergeneai-dashboard/scraper.py` | Google Places API (New) client + geocoding |
| main.py | `/home/hermes/ergeneai-dashboard/main.py` | FastAPI backend with CRUD + scrape + analyze endpoints |
| index.html | `/home/hermes/ergeneai-dashboard/index.html` | Single-page dashboard with map + analysis + messages |
| leads.json | `/home/hermes/ergeneai-dashboard/leads.json` | All lead data including analysis + message fields |
| google-oauth.json | `/home/hermes/ergeneai-dashboard/google-oauth.json` | OAuth credentials for future Gmail/Calendar |

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/leads` | List leads (filter: status, search, niche) |
| GET | `/api/leads/geocode` | Geocode leads missing coordinates |
| POST | `/api/leads` | Add lead manually |
| PUT | `/api/leads/{id}` | Update lead (status, notes, etc.) |
| DELETE | `/api/leads/{id}` | Delete lead |
| GET | `/api/stats` | Summary stats |
| POST | `/api/scrape` | Google Places API scrape → auto-add to CRM |
| POST | `/api/analyze` | Analyze ALL leads → generate messages |
| POST | `/api/analyze/{id}` | Analyze single lead |

## Google Places API (New) — Quick Reference

```python
# Endpoint
POST https://places.googleapis.com/v1/places:searchText

# Headers
Content-Type: application/json
X-Goog-Api-Key: <YOUR_API_KEY>
X-Goog-FieldMask: places.displayName,places.location,places.rating,
                   places.userRatingCount,places.internationalPhoneNumber,
                   places.formattedAddress,places.websiteUri

# Body
{"textQuery": "güzellik salonu Mudanya", "languageCode": "tr", "maxResultCount": 15}

# Response field mapping
place["displayName"]["text"]              → name
place["location"]["latitude"]             → lat
place["location"]["longitude"]            → lng
place["internationalPhoneNumber"]         → phone
place["formattedAddress"]                 → address
place["websiteUri"]                       → website
place["rating"]                           → rating
place["userRatingCount"]                  → reviews
```

## Priority Classification

```python
if "website" in needs → priority = "high"    # No site = biggest opportunity
elif needs → priority = "medium"             # Has site but needs work
else → priority = "low"                      # Good digital presence
```

## Message Template Structure

```
Merhaba [işletme] yetkilisi,

Ben ErgeneAI'den Bilal. [web durumuna göre kişisel giriş]

[ihtiyaç listesine göre çözüm önerileri]

[kapanış - sektöre özel CTA]

Teşekkürler,
Bilal Ergene
ErgeneAI — Dijital Çözümler
```

## Nominatim Geocoding Rate Limits

- 1 request/second max
- User-Agent header ZORUNLU (proje adı + email)
- Free, no API key needed
- Falls back to city-level coordinates if address not found

## What's Next (Planned)

- Gmail SMTP integration (OAuth flow, app password or token)
- Google Calendar appointment scheduling
- Send analysis report via email
- Track open/response rates
- n8n workflow for automated follow-up sequences
