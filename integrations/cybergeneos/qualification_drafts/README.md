# Qualification report to first-contact draft

An owner or Jeff can start a native `marketing` job with
`source=qualification` for one current, source-backed meeting candidate.
The card also offers **Güncel kanıttan taslak hazırlasın**. The legacy research
path retains its gate requirement; this path uses the newer qualification
contract without writing a gate override or an owner decision.

The job reopens the report's supported and counter sources, requires the same
quotations and source-text fingerprints, and records the observation. Changed
or unreadable evidence invalidates that qualification report until a new
report is produced. Only source-matching evidence reaches the writer.

Jeff writes one first-contact message and examines it in a separate session.
The critic links literal message fragments to verified fact IDs, explains the
strongest alternative, states the evidence limit and records a condition that
would disprove the proposal. A refused or malformed critique cannot publish a
ready draft. This is a second model reading, not independent field validation.
The official-source statements, actual workload, need and purchase intent
remain separate. Neither a message volume nor a missed appointment is inferred.

Both model calls use immutable job IDs and durable checkpoints. An unrecorded
response is uncertain; it is never automatically charged again. There is no
silent revision loop. The existing default limit of five marketing jobs per
rolling 24 hours remains, with cost unknown where no price receipt exists.

The saved draft includes its report identity/digest, service capability digest,
message/fact links and critic receipt. A newer report (even with the same text),
expiry, company/contact change, opt-out, capability change or draft/metadata
change revokes currentness and owner feedback. Source observations are point
in time: arbitrary later website changes are discovered on the next source
read or report refresh, not continuously monitored by this feature.

The native owner-only review endpoint stores acceptance/rejection against the
current draft. Jeff's token cannot submit owner feedback. This pilot keeps the
message read-only; a change is a new job with an optional tone note and a new
critique. The card provides review and copying, with no delivery button. No
delivery, booking, owner approval or customer outreach is performed by this job.
The existing delivery guard also refuses stale or unreviewed qualified drafts.

## Replay and validation

This package follows the previously installed `lead_qualification` package.
It contains the canonical marketing/qualified-draft modules, a bounded patch
for the other selected panel files, the full panel tests and fingerprints:

```text
python install.py --repo-root /path/to/cybergene-web
```

The default stages and verifies all nine target files. An already installed
version is a no-op. Other versions must be reconciled, not forced. `--apply`
backs up the selected original sources outside the checkout. It does not
restart a service or alter a database. On startup the source-invalidation table
is additive. Back up SQLite online and wait for active jobs before deploying.

The repository SQLite adapter tests storage, source binding, owner-review
revocation and uncertainty. The packaged panel tests exercise the full model,
source, HTTP action and application adapters in the separate panel checkout.
See the deployment report for actual platform and live-pilot results; packaged
tests are not automatically the complete panel suite in this repository CI.
