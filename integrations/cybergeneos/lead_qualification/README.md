# Select meeting candidates by evidence

The existing panel can find firms, but its fixed gate can promote missing website
features into presumed pain. This integration adds a separate shortlist capped at
ten distinct official domains. It does not pad the list to ten, create outreach,
approve drafts, or claim a meeting probability or purchase intent.

## Admission

1. Read current official pages (up to eight collector requests and four extra
   quoted sources). Public URL, redirect and robots checks reuse the panel reader.
   Shared directories are excluded. Eligibility uses the existing target sectors;
   ambiguous old gate results do not exclude a company from this new examination.
   Career/HR, contact, FAQ and booking/cancellation terms take priority; discovery follows at most two
   link levels. Full fetched text remains available to quote checks while the
   model receives bounded excerpts that preserve process details after menus.
2. Jeff proposes at most eight quoted facts and a service from the existing
   capability catalogue. Generic appointments, treatment lists, missing chat,
   website omissions and healthcare price publication are insufficient signals.
3. Code reopens new quotation sources and checks exact normalized quotation,
   domain, retrieval time and source digest. This verifies publication, not the
   firm's internal situation or the model's interpretation.
4. A separate Jeff call critiques entailment, distinct workflows, capability fit
   and contradictory existing solutions. This is another reading by the same
   model, not an independent ground-truth observer. Invalid evidence references
   fail closed. Source content remains untrusted data in both calls. The model receives only
product capabilities, without the old gate's keyword/absence heuristics. A
WhatsApp link or form alone does not prove an existing automation solution.
5. Code requires service fit, an explicit stated problem OR two different concrete
   workflows, a currently published business contact, a discovery question and
   no supported blocking counter-evidence. Need remains a hypothesis until a human
   conversation. A public phone number does not verify WhatsApp availability;
   publishing an email does not verify deliverability or reach a decision-maker.

## Instagram and mandatory adversarial decisions

Official Meta Business Discovery now reads publisher biographies and up to four
recent publisher captions per verified business profile. It uses Facebook Login,
Graph API v25.0, a fixed provider origin, GET requests, bounded responses, no
automatic retries or pagination and bearer headers. Redirects never forward
credentials. Missing/expired permissions or unavailable accounts remain unknown;
the trusted public-browser fallback remains available without bypassing robots.
Generic Instagram /p and /reel permalinks are admitted only from collected API
receipts with an exact matching publisher, current website identity link and
retrieval freshness. Existing browser author/path checks are unchanged.
Publication time is preserved separately; it does not establish an event date,
internal message volume, response time, booking loss or unmet need. Images,
videos, comments and third-party private messages are not collected. Publisher
captions can contain testimonials; these do not establish unmet operational need.

Install only the access token and business account ID in a mode-600 private
`CGOS_DATA/meta-instagram.json` file outside the repository and served directories
(override: `CGOS_META_INSTAGRAM_CREDENTIALS`). Required shape:
`{"access_token":"<private token>","business_account_id":"<account ID>","version":"v25.0"}`.
No app secret or webhook verification token is required for this collector.
Credentials, raw provider errors and authentication headers never enter the
research/model payload, UI, receipts or logs.

Each research run finds Instagram profiles linked from current official website
pages (at most three accounts). Exact host/path validation excludes lookalikes,
login URLs and unrelated profiles. A readable public profile needs matching
publisher metadata. Unreadable content is recorded as unknown, never an absent
channel, delayed response or presumed lost booking.

For the pilot, a trusted collector can save public browser receipts under
`CGOS_DATA/instagram-evidence/<handle>.json` (or `CGOS_INSTAGRAM_EVIDENCE_DIR`).
These are operator-controlled files, not model text or API inputs. The current
website must still link that exact account; profile receipts expire after 24
hours. Up to four captured publisher captions can be used only when their post
URLs appeared in the profile and their visible author matches the handle.
Source time, text digest, website identity link and collection scope remain in
the report. This supports public evidence collected in a real browser; it does
not mean the server has an autonomous browser crawler, access to DMs, or access
to private accounts. Third-party comments are not imported as publisher captions;
testimonials do not establish unmet operational need. A snapshot proves what was
read then, not today's live text.
Official business contact scoring continues to use website sources only.

The separate Jeff audit now must provide all three: the strongest alternative
explanation, what the evidence cannot establish, and a concrete observation
that would disprove the proposal. Missing reasoning prevents admission even if
the score passes. The panel shows this reasoning and Instagram coverage.
Previously admitted reports without this expanded audit stay stored but are
withdrawn from the current shortlist until explicitly re-examined. Staff or a
job opening alone is not blocking counter-evidence, and hiring is not software
purchase intent. The same model's adversarial reading is not independent field
validation. Follower counts, showroom photos and campaign frequency do not
establish workload or a bottleneck.
The critic receives only the verified fact list with its new IDs. Unverified
research quotations are omitted from the audit payload. Equivalent official URLs
share their collected page instead of wasting the four extra-source allowance.
Rejection text reflects the actual admission checks; the model's original reason
is preserved separately and cannot present an unsupported positive conclusion.

Clinical image interpretation, diagnosis and medical treatment-plan preparation
cannot count as an administrative callback. A generic digital-follow-up heading
does not prove appointment reminders or another administrative follow-up workflow.
A response-time promise cannot count as an explicit backlog; a named coordinator
does not establish that a single employee handles all messages. When unsupported
signals are removed from a legacy candidate, the view gives a bounded hypothesis
using the remaining administrative workflows and preserves the original text.
The critical reading also distinguishes clinic opening hours from separate support
channel availability. Current views apply this service boundary to older candidates;
when one loses its basis, the original model record/score remains stored and its
current view explains the withdrawal without another paid model call.

Priority points: service fit 25, need signals 0/10/30, current official email 20 or
phone 15, dated recent event 15. Admission requires at least 70/90 plus all hard
conditions. These are policy points, never calibrated probabilities. Timing points
require a literal event date in a source-checked date quotation, at most 90 days
old and not in the future. Page retrieval time is not an event date.

## Persistent jobs and presentation

`qualification` jobs reserve a bounded company batch (maximum 40 per batch and,
by default, per rolling day, `CGOS_QUALIFICATION_DAILY_CAP`). Reservations count
even when a run fails, preventing cheap-looking retries from hiding model costs.
Same request identities reuse the original job and reject changed lists.

Each completed company report publishes with its checkpoint in one transaction.
Restart keeps completed reports. An in-flight model response without a saved
result is marked uncertain and is never automatically charged again. Other never-started
companies can continue; malformed received responses are isolated and not retried.
ASCII JSON key names with curly quotation delimiters can be normalized without
another model call. The original response and a repair receipt remain stored;
quoted values are never rewritten. Duplicate keys, malformed values, truncated
objects and multiple objects still fail closed. This syntax repair cannot bypass
quotation verification or the mandatory adversarial admission conditions.
Default batch selection excludes fresh reports and recent unresolved attempts;
explicit individual requests can re-examine a firm within the reserved daily cap. The current
implementation checkpoints completed companies, not each internal model call;
an interrupted research/critique pair needs explicit reconciliation. Provider
usage is stored for completed reports; trustworthy monetary cost is unknown.
Collector request limits and daily company reservations do not impose a hard
token or web-tool-call budget on the Hermes agent loop. Prompt page limits and
the requested completion token limit must not be described as enforced spend caps.

Reports expire after 14 days, or disappear from the shortlist when company inputs
change, the firm opts out, or it passes first-contact stages. A shortlist dedupes
official domains, not all possible corporate brands; companies using multiple
domains and branch-level attribution still need review. No old lead/draft/contact
data is overwritten. Skipped unreadable firms appear in job checkpoints rather
than fabricated reports.

The panel adds **Görüşme adayları**, the selection action and an evidence dossier:
conditional need, service match, current contact, timing, counter-evidence,
unknowns and a discovery question. Jeff's state/summary includes the shortlist.
Existing draft and delivery controls remain separate owner actions.

## Replay and validation

Run `python install.py --repo-root /path/to/cybergene-web` to stage the patch against
the fingerprinted 2 October panel baseline; add `--apply` to install source only.
It accepts LF/CRLF, refuses concurrent source changes, backs up replaced files and
does not touch databases, services, secrets or model configuration.

Run `tests/test_qualification.py` in the separate panel checkout: thirty-four tests
exercise generic/duplicate/unsupported evidence rejection, blocking counters,
event dating, official contact, request identity, reserved budget, restart
ambiguity, real SQLite publication, stale/opt-out exclusion, list cap and cancel.
The complete panel suite passed 112 tests on Windows before activation; the response-isolation repair
passed updated qualification tests and the six root adapter tests.
The staged Linux panel passed 138 tests after Instagram, source-depth, verified-only
audit inputs, mandatory adversarial reasoning, booking-policy discovery and safe JSON-key normalization. Thirty-four qualification and six Meta integration tests passed
on Windows. Root Jeff
CI runs a small SQLite adapter test suite of the packaged module; it is not the
full separate panel or an assessment of real sales performance.

Business acceptance needs owner feedback and subsequent contact/reply/meeting
outcomes. Ten source-backed recommendations do not mean ten confirmed needs or
ten meetings. Private leads, report texts, database backups and credentials are
excluded from this package.

Meta access was supplied and verified on 3 October 2026. The staged server
collector read four real website-linked business profiles and ten publisher
captions. The connected own account is `cybergene.ai`. Read access and permission
grants were verified without posting, commenting or sending messages.

The user also authorized full Instagram account management. The credential has
content publishing, comment management, insight and messaging permissions. Those
grants do not prove that each management workflow is implemented or usable for
every conversation. This package activates research only; own-account publishing,
comment operations and eligible conversation handling need separate durable
execution and reconciliation. See [INSTAGRAM_META_TODO.md](INSTAGRAM_META_TODO.md).
Third-party profiles are research sources, never accounts Jeff can manage.
