# Company research and draft workflow

The first marketing-base workflow joins the panel's existing restricted Jeff
research profile and first-contact writer. A lead card offers **Jeff incelesin
ve taslak hazırlasın**. This package contains only the selected integration;
the separate cybergene-web checkout has other ongoing user work.

## Result and boundaries

- One company per persistent `marketing` job. HTTP request identities and aliases
  remain idempotent after completion. Default cap: five runs per rolling 24 hours
  (`CGOS_MARKETING_DAILY_CAP`); model prices are not assumed.
- The research profile must report only the `web` toolset. Jeff reads the firm's
  official site; the panel reopens quoted pages, checks domain/redirects, respects
  robots rules and discards quotations it cannot find. Website claims remain
  publisher claims. A quote match does **not** verify the model's interpretation,
  missing features, actual need or purchase intent.
- The managed writer receives verified quotations and product capabilities,
  without the research model's inferred findings. Hypotheses are labeled in the
  card. No verified finding means no generated draft.
- Research and draft checkpoints survive restart. A response that was in flight
  without a recorded result is marked uncertain and never automatically repeated.
  An explicit new run may incur another model charge.
- Both results, the lead update and one event publish in a single transaction.
  Changes to the company, draft, opt-out or contact stage prevent an overwrite.
- Owner feedback (`accepted`, `rejected`, `edited`) is bound to a content digest.
  An edit invalidates the prior decision. Review endpoints require the existing
  panel-owner login; Jeff's automation token cannot access them. This is draft
  feedback, **not** a complete migration of the separate legacy approval stores.
- The workflow never calls a customer delivery action. Existing panel delivery
  controls remain separately available to its owner. Completion means saved
  source-checked drafts, not delivery or fully autonomous marketing.
- Actual step duration and provider-reported token usage are recorded. Cost is
  `null` when no trustworthy price receipt exists.

## Replay

The checked baseline and target fingerprints are included. Live secrets and
private lead records are excluded; in particular the legacy connection module's
credential fallback is replaced without putting its value in a diff.

From this package:

```text
python install.py --repo-root /path/to/cybergene-web
```

The default stages the patch in a temporary copy and checks every target
fingerprint. LF and CRLF source are supported. Already-installed targets are a
no-op. Other source versions require reconciliation; do not force the patch.
For installation, provide the private `HERMES_API_URL` / `HERMES_API_KEY`
environment and add `--apply`. The backup goes outside the repository and may
contain private legacy source; do not publish it. The installer does not restart
services, modify databases or create the research profile. Test against a staged
copy, back up the online SQLite database, and restart the panel only when no jobs
are active. The three marketing tables are additive.

The safe `server/jeff.py` also restores a distinct panel conversation and makes
**Yeni sohbet** open a new session. It retains the established data/instruction
boundary; the main profile's shared identity and memory remain available.

## Validation, 2 October 2026

- Separate panel: 85 existing regression tests + 13 workflow tests on Windows;
  98 tests passed on the staged Linux panel after the final grounding adjustment.
  Source-claim fixtures come from the local site source; these tests do not prove
  the current public website has deployed every product capability.
- Jeff repository: four real SQLite persistence-boundary tests with a small
  panel adapter, included in root pytest. The full panel tests are supplied here
  for running in its own checkout and are not treated as this CI's full coverage.
- Target patch replayed against the captured baseline and all nine fingerprints
  matched. Fatal Python checks and JavaScript syntax passed.
- Live Dent Nilüfer pilot completed; the first run exposed overconfident inferred
  headings, so hypotheses were labeled and the writer input narrowed to quotations.
  The revised run produced three source-checked findings and channel drafts in
  73.13 seconds of recorded step time. No owner acceptance or delivery was recorded.
- The browser showed the result/review controls; retrying an existing request
  reused its job. Request identity also works on the panel's current HTTP address.

Acceptance of business value still needs Bilal's feedback on the first five
different companies: usefulness, fact corrections, edits and hands-on review time.
Automated sending, durable radar jobs, general GUI verification and cognitive
dependency reconstruction are outside this milestone.
