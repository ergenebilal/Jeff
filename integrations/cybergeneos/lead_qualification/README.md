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
2. Jeff proposes at most eight quoted facts and a service from the existing
   capability catalogue. Generic appointments, treatment lists, missing chat,
   website omissions and healthcare price publication are insufficient signals.
3. Code reopens new quotation sources and checks exact normalized quotation,
   domain, retrieval time and source digest. This verifies publication, not the
   firm's internal situation or the model's interpretation.
4. A separate Jeff call critiques entailment, distinct workflows, capability fit
   and contradictory existing solutions. This is another reading by the same
   model, not an independent ground-truth observer. Invalid evidence references
   fail closed. Source content remains untrusted data in both calls.
5. Code requires service fit, an explicit stated problem OR two different concrete
   workflows, a currently published business contact, a discovery question and
   no supported blocking counter-evidence. Need remains a hypothesis until a human
   conversation. A public phone number does not verify WhatsApp availability;
   publishing an email does not verify deliverability or reach a decision-maker.

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
companies can continue; malformed received responses are isolated and not retried. The current
implementation checkpoints completed companies, not each internal model call;
an interrupted research/critique pair needs explicit reconciliation. Provider
usage is stored for completed reports; trustworthy monetary cost is unknown.

Reports expire after 14 days, or disappear from the shortlist when company inputs
change, the firm opts out, or it passes first-contact stages. A shortlist dedupes
official domains, not all possible corporate brands; companies using multiple
domains and branch-level attribution still need review. No old lead/draft/contact
data is overwritten. Skipped unreadable firms appear in job checkpoints rather
than fabricated reports.

The panel adds **GÃ¶rÃ¼ÅŸme adaylarÄ±**, the selection action and an evidence dossier:
conditional need, service match, current contact, timing, counter-evidence,
unknowns and a discovery question. Jeff's state/summary includes the shortlist.
Existing draft and delivery controls remain separate owner actions.

## Replay and validation

Run `python install.py --repo-root /path/to/cybergene-web` to stage the patch against
the fingerprinted 2 October panel baseline; add `--apply` to install source only.
It accepts LF/CRLF, refuses concurrent source changes, backs up replaced files and
does not touch databases, services, secrets or model configuration.

Run `tests/test_qualification.py` in the separate panel checkout: fifteen tests
exercise generic/duplicate/unsupported evidence rejection, blocking counters,
event dating, official contact, request identity, reserved budget, restart
ambiguity, real SQLite publication, stale/opt-out exclusion, list cap and cancel.
The complete panel suite passed 112 tests on Windows before activation; the response-isolation repair
passed the updated fifteen qualification tests and the five root adapter tests.
The final staged Linux panel passed 113 tests. Root Jeff
CI runs a small SQLite adapter test suite of the packaged module; it is not the
full separate panel or an assessment of real sales performance.

Business acceptance needs owner feedback and subsequent contact/reply/meeting
outcomes. Ten source-backed recommendations do not mean ten confirmed needs or
ten meetings. Private leads, report texts, database backups and credentials are
excluded from this package.
