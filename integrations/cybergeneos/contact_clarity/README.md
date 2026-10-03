# Contact purpose and sender clarity

The decision-first pilot previously displayed only the draft's closing question, separating it from its introduction. Show the draft's real `scope` under “Temas amacı” instead. For older drafts containing the schema placeholder, show their opening context. Keep the complete original draft and its heading inside “Taslağın tamamı”; feedback and copying still read the full text. Laptop layouts are the primary acceptance target (1366×768 and 1280×720), with mobile compatibility retained.

A live corrective generation also revealed a wrong sender attribution that the model critic approved. Policy version 3 now fixes the opening sender sentence, rejects conflicting openings even with a positive critic, rejects the generic scope placeholder, and asks both generation and critique for concise, natural wording with a concrete conditional administrative benefit. Existing quote verification, channel/context limits, claim mappings and the separate critical reading remain required. Prior policy drafts become stale; their stored job outputs and owner history are retained. New text must come from a fresh native Jeff job. No customer delivery or owner acceptance is performed by this integration.

The incremental installer covers only `app.js`, `server/qualified_draft.py` and its tests, based on the deployed decision-first source. It rejects source drift, stages fingerprinted patch replay and preserves a source backup. Coordinate a backend service restart only when no jobs are active; the installer does not restart services or modify databases. The canonical qualification-draft bundle also carries the updated policy and tests for new installations.

```sh
python3 integrations/cybergeneos/contact_clarity/install.py --repo-root /home/hermes/cybergeneos
python3 integrations/cybergeneos/contact_clarity/install.py --repo-root /home/hermes/cybergeneos --apply
```

Validation: regressions for a misattributed sender approved by the critic, a placeholder purpose, and stale old-policy drafts; the full panel suite; fingerprinted replay, dry-run, idempotency and source-drift refusal. Browser validation uses an isolated real-panel preview: purpose, decisions and closed disclosures fit the laptop viewport; all existing text, links and actions remain available; the clipboard gets the complete draft. Actual draft generation and its evidence/critic record are checked separately on the native job. A positive model critique alone does not independently prove business need or language quality.
