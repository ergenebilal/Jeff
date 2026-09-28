# Live-Site Fix Protocol (27.07.2026)

## When the user reports a bug on a live site

Trigger: user says "görünmüyor", "çalışmıyor", "hala aynı", "bozuk", "düzelmemiş", "şu işi kalıcı olarak hallet", or similar frustration about a deployed site.

## Procedure

### Phase 1: Full Discovery (do NOT apply fixes yet)

Read the ENTIRE relevant file first. Find ALL instances of the problem pattern, not just the first one. Common issues found together:

- Broken emoji rendering → often accompanies broken HTML attributes
- `data-i18n` outside tag → check every occurrence of the pattern
- Missing cache-control headers
- Reverse proxy cache (Traefik, Caddy)
- CSS visibility (responsive classes hiding elements)
- JavaScript errors preventing execution

Run these checks:

```bash
# Check container file
docker exec container-name grep -n 'pattern' /path/to/file

# Check all data-i18n attributes (are they inside tags?)
docker exec container-name grep -n 'data-i18n=' /path/to/file | head -30

# Check responsive CSS
docker exec container-name grep -n 'desktop-only\|mobile-only\|@media' /path/to/file

# Check HTTP response from public URL
curl -sI https://domain.com | grep -iE 'cache|pragma|age'
```

### Phase 2: Apply ALL Fixes at Once

List every issue found, then fix them ALL before reporting back.

### Phase 3: Verify on Public URL

```bash
# Verify container file
docker exec container-name grep -n 'changed text' /path/to/file

# Verify nginx serves it correctly
docker exec container-name curl -s http://127.0.0.1/ 2>/dev/null | grep 'changed text'

# Verify public URL
curl -s https://domain.com | grep 'changed text'

# Check reverse proxy (if present)
docker inspect proxy-container --format '{{.Config.Image}}'
docker inspect app-container --format '{{json .Config.Labels}}' | grep -i 'middleware'
```

### Phase 4: Report

Message structure:
1. **Issues found** (numbered list)
2. **Fixes applied** (one per issue)
3. **Verification** (link to confirm it works)
4. **User action needed** (hard refresh / incognito)

### Frustration Escalation Signals

| Signal | Meaning | Action |
|--------|---------|--------|
| "hala aynı" (2nd time) | Fix didn't land, or cache issue | Check public URL directly |
| "görünmüyor" + screenshot | Visual rendering issue | Open screenshot, compare with expected output |
| "farklı tarayıcı" test done | Not cache, something actually wrong | List ALL remaining issues, fix at once |
| "şu işi kalıcı olarak hallet" | Patience exhausted | Stop incremental fixes. Full investigation + all fixes + verified on live URL before reporting back. |
