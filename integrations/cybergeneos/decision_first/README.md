# Decision-first candidate card

This incremental patch extends the existing separate panel. Başiskele (`lbc4b1bd986`) is the card pilot; other cards retain the existing workspace. All meeting-candidate list rows show a short hypothesis excerpt with a native `(neden?)` disclosure containing the original full line.

The pilot puts the existing name/location header, one-sentence reason, three-line excerpt from the actual draft, and the original acceptance/rejection/copy buttons first. The complete read-only draft, rationale (including scores and both critical readings), evidence (including claim mappings, quotations, links and Instagram limitations), and company information are retained in closed native disclosures. No actions or feedback handlers are replaced; the copy handler still reads the complete `#c-text`, even when its disclosure is closed. Existing draft readiness guards remain in force. There is no sending action on the pilot.

Only `app.js` and `index.html` change. `serve.py`, API handlers and databases remain unchanged. The installer defaults to dry-run, rejects unfamiliar source fingerprints, checks patch replay and retains a private source backup before application. It does not restart services.

```sh
python3 integrations/cybergeneos/decision_first/install.py --repo-root /home/hermes/cybergeneos
# After reviewing the dry-run:
python3 integrations/cybergeneos/decision_first/install.py --repo-root /home/hermes/cybergeneos --apply
```

Validation uses the actual panel in an isolated local preview with captured current lead data and mock API responses; no live owner decisions are submitted. Check 1440×900, 390×844 and 320×568: company, reason, preview and all three buttons visible before scrolling; rationale/evidence closed; opening each exposes its original content. Compare every original text node, hyperlink, action and full textarea value before and after reordering. Accept/reject must keep the original endpoint, draft digest and full text; copy must put the full draft on the clipboard. A stale draft must not acquire decision buttons. Native list disclosures must expand without opening a card. Also check patch fingerprints and JavaScript syntax. Preview data and browser artifacts are intentionally excluded from this bundle.
