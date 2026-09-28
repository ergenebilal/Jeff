# PR-04 — CI, secret protection and repository hygiene

## Result

Seven named GitHub Actions jobs cover active compile, Bridge unit tests,
Jeff–Pablo contract tests, fatal lint rules, current tracked secret scan,
dependency audit, and task schema validation. The test runner uses unittest
from the repository root. The old duplicate contract fixture test module was
renamed and excluded from the active suite; live coding Bridge tests remain
active. The intentionally broken sandbox fixture has a separate negative test.

The active manifest limits compile and lint to real production files. Ten
`API_KEYS.md` template files were renamed to `API_KEYS.example.md`, and
installer references were updated. Six invalid one-line absolute-path Python
stubs were replaced by `LEGACY_IMPORTS.json`. `.bak`, temporary files, and
the bootstrap environment are ignored; no tracked `.pyc`, database, or log
files were present.

## Secret findings and required rotation

The current tracked-file scan reports zero high-confidence findings after
moving literal credentials in the Apollo, Reddit, and daily bulletin scripts
to environment variables. These scripts now fail closed if credentials are
missing. The available Git history contained credential-like objects,
including Telegram, OpenAI, AWS, and Slack patterns. No values were printed.
History rewrite is deliberately out of scope. Owners must revoke and rotate
each real credential at its provider, update service secrets, and then enable
GitHub secret scanning and push protection. A pattern finding may be a fixture;
the owner must classify it without posting values in a PR or issue.

## Local verification

```bash
python scripts/bootstrap_active.py
python scripts/compile_active.py
python scripts/check_negative_fixture.py
python scripts/ci_secret_scan.py
python scripts/ci_secret_scan.py --history --summary-only
python scripts/validate_task_schema.py
```

The bootstrap creates `.venv-active`, installs existing Bridge requirements,
and runs the active unittest suites. CI-only tools are Ruff (MIT), pip-audit
(Apache-2.0), and jsonschema (MIT). They are used respectively for fatal lint
rules, dependency vulnerability checks, and Draft 2020-12 schema validation;
none is added to production requirements.

## Branch protection checklist

In GitHub repository settings for `main`:

1. Block direct pushes and force pushes.
2. Require at least one review and dismiss stale approvals after new commits.
3. Require all seven jobs in `.github/workflows/active-contract-gates.yml`.
4. Require conversation resolution before merge.
5. Block branch deletion.
6. Enable secret scanning and push protection; review the history findings
   privately and rotate exposed credentials.

## Rollback

```bash
git switch codex/pr-03-real-briefing-radar
```

For a deployed checkout, restore reviewed files from the previous release and
restart the Bridge service. Keep SQLite task and report records. CI and branch
protection settings are separate GitHub settings and can be reverted there.

## Remaining risks

The historical secret objects remain accessible until credentials are rotated.
The repository is a partial clone, so a history scan must be evaluated against
all fetched blobs and GitHub's server-side secret scanning. Existing large
binary history is retained. CI checks apply only after the branch is pushed
and must be made required in repository settings by an administrator.
