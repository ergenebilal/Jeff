# Automatic current-source mirror

Branch: `codex/automatic-jeff`. This is a managed source snapshot, not a deployment and not a claim of general Jarvis acceptance. The source checkout, index, development branch, production services, databases, model settings and business rules are never changed by the publisher.

The server checks current tracked and unignored source every minute. Source bytes must remain unchanged for at least 60 seconds. All writing tools use the same file observation path; no tool-specific hook or successful exit-code assumption is needed. Windows installed Python source and its recovery helper are privately collected every two minutes, then pass the same publication checks. Existing server installed source listed in the current recovery inventory is captured separately under runtime-source/server; installed Windows source is under runtime-source/windows. These are installed-on-disk snapshots, not proof that a process has reloaded them.

Private notes, secrets, runtime configuration, databases, logs, reports, screenshots, backup copies, uninstalled future experiments and the deliberately private Windows human-behavior layer are excluded. Known literal owner IDs are replaced by TELEGRAM_OWNER_CHAT_ID configuration in the PUBLIC COPY only. The personal adviser template uses request context in the public copy. Unknown private template shapes, new credential literals, syntax errors and racing source changes block publication. One existing intentionally broken sandbox fixture has an exact-byte syntax exemption; changing it does not bypass validation. One pre-existing credential-like reference is explicitly retained privately pending review.

No private local commit history is pushed. Stable safe bytes are committed in an isolated clone. Network errors preserve the pending source snapshot. A diverged public history blocks, with no force push, reset, production rebase or source replacement. Unchanged content adds no commit. Successful publication requires reading the target commit back from GitHub. The main development branch remains separately maintained.

Preparation checks: 25 independent tests on Windows and Linux, including local Git remotes, source races, private settings, retry preservation, history divergence and Windows packet integrity. Actual scheduler-to-GitHub acceptance is recorded in the private operational evidence after installation.

## Actual transport evidence

The new server timer completed its first publication and the target commit was independently read back from GitHub. The Windows collector completed a real scheduled private packet transport. Subsequent source updates are handled by the same timer and gates; this document update is included in that ordinary flow. Current task acceptance is held privately, including recovery/rollback evidence and coverage exclusions.
