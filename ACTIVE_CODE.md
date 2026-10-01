# Active source map

`ACTIVE_CODE.json` is the machine-readable source manifest used by compile and
lint jobs. The active Bridge entrypoint is `jeff2/bridge/jeff_bridge_api.py`;
`jeff2/bridge/jeff-bridge.service` is its Linux service file. The Pablo entry
is `pablo/hermes_node.py`, with `pablo/pablo_task_guard.py` as the action
boundary. Task state and verification live in `jeff2/bridge/task_contract.py`.
The installed cron entries use `scripts/morning_report.py`, `scripts/lead_alert.py`,
`scripts/system_watchdog.py`, and `scripts/jeff_backup.py`. Approval totals are
shared through `scripts/approval_inventory.py` and authenticated Pablo heartbeat
snapshots. `scripts/model_health.py` is the model diagnostic entrypoint. Older
briefing/radar implementations remain listed as compatibility modules.
Marketing modules and all modules run by the active test runner are included in
the compile/lint manifest, so these checks cover the deployed changes.

`jeff2/_on_hold`, `scripts/_archive`, and `jeff2/self_healing_sandbox` are not
production import paths. `jeff2/bridge/contract_tests` contains isolated
fixtures; only its named contract test is in the active test suite. Former
one-line absolute-path Python stubs are listed in `LEGACY_IMPORTS.json` and
removed from executable Python paths. Their Git history remains available.

From a clean checkout, run all active tests with one command:

```bash
python scripts/bootstrap_active.py
```

For pytest, install `pytest>=8,<10` alongside the Bridge requirements and run
`pytest` from the repository root. No manual PYTHONPATH is needed. The default
selection matches the active Bridge/Pablo/operations group; it excludes archived
and manual live probes. The Linux contract fixtures use names that overlap
production modules and must run separately with
`python scripts/run_active_tests.py --group contract`. Run both groups with the
existing bootstrap or `python scripts/run_active_tests.py --group all`.
The approval inventory test also runs independently with either pytest or
`python -m unittest scripts.test_approval_inventory`.

For manual Bridge rollout after review and backup, copy the reviewed Bridge
files to `/home/hermes/jeff2/bridge`, then run on the Linux host:

```bash
sudo systemctl restart jeff-bridge
curl -fsS http://127.0.0.1:7700/health
```

The Windows Pablo rollout uses its own reviewed package at
`C:\CyberGene\HermesNode`. The CI workflow never deploys or sends messages.

Large existing MP4/PDF files stay in Git for compatibility. Before adding new
media, store large binary releases in Git LFS, GitHub Releases, or object
storage and link them from source. Moving existing historical blobs would
rewrite history and is not part of this PR.
