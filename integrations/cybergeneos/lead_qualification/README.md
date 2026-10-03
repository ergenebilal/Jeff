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
   Career/HR, contact and FAQ links take priority; discovery follows at most two
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
to private accounts. Comments and patient testimonials are not imported as
publisher captions. A snapshot proves what was read then, not today's live text.
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

Run `tests/test_qualification.py` in the separate panel checkout: twenty-seven tests
exercise generic/duplicate/unsupported evidence rejection, blocking counters,
event dating, official contact, request identity, reserved budget, restart
ambiguity, real SQLite publication, stale/opt-out exclusion, list cap and cancel.
The complete panel suite passed 112 tests on Windows before activation; the response-isolation repair
passed updated qualification tests and the five root adapter tests.
The staged Linux panel passed 125 tests after Instagram, source-depth and
mandatory adversarial-reasoning changes. Twenty-seven qualification tests passed
on Windows. Root Jeff
CI runs a small SQLite adapter test suite of the packaged module; it is not the
full separate panel or an assessment of real sales performance.

Business acceptance needs owner feedback and subsequent contact/reply/meeting
outcomes. Ten source-backed recommendations do not mean ten confirmed needs or
ten meetings. Private leads, report texts, database backups and credentials are
excluded from this package.
