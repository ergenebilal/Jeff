# PR-01 live deployment record — 2026-09-28

PR-01 was deployed to the Jeff Bridge systemd service and the live Windows
Pablo worker. The live Bridge source matched the repository's `main` version.
The live Pablo worker contained additional features, so only the PR-01 Bridge
protocol changes were ported; its TaskGuard implementation was preserved.

Before activation, a consistent copy of the live SQLite database and eight
server files was saved under `/home/hermes/pr01-20260928-deploy-backup`.
The Windows worker, configuration, and TaskGuard were saved under
`C:\CyberGene\change-backups\pr01-20260928-deploy`. These backups contain
historical credentials and must remain access restricted.

The Bridge key was rotated. The new key is held in `/etc/jeff-bridge.env`
with owner `root`, group `hermes`, and mode `0640`; the Windows Pablo config
holds the same key. The Bridge and both Telegram bot services load that file.
The Bridge explicitly binds all interfaces so localhost Jeff clients and the
Tailscale Pablo worker can both connect; its exact IP allowlist admits the
Pablo Tailscale address and loopback clients.
Temporary staging copies of the key were removed. Do not restore the old
Windows config or the old inline-key systemd unit.

Post-deployment checks:

- Bridge and both bot services: active, zero restarts and zero main-process errors.
- Bridge health over Tailscale: HTTP 200, Aider ready, Pablo online.
- Live read-only `ping` task: `pr01-deploy-ping-50b410e4d710`.
- Pablo TaskGuard response: `SUCCESS`; Bridge result: `unverified`, `ok=false`.
- SQLite: one event and one result for that task; all previous 38,745 events
  were preserved, followed by the new event.
- No browser, message, or customer-facing action was used for the smoke test.

Emergency source rollback, if needed: stop the Bridge and Pablo worker,
restore only `jeff_bridge_api.py` from the server backup and `hermes_node.py`
from the Windows backup, then restart the worker and Bridge. Keep the new
`BRIDGE_KEY` and service environment file. The old source ignores the additive
SQLite columns and tables. This rollback reintroduces the old Bridge security
weaknesses and should only be temporary. Do not restore the database backup
over a live database: that would discard tasks created after deployment.

After stopping Pablo, restore the server source with:

```sh
ssh hermes 'cp /home/hermes/pr01-20260928-deploy-backup/home/hermes/jeff2/bridge/jeff_bridge_api.py /home/hermes/jeff2/bridge/jeff_bridge_api.py && sudo systemctl restart jeff-bridge.service'
```

On Windows, restore the worker source while leaving `config.json` untouched:

```powershell
Copy-Item -LiteralPath 'C:\CyberGene\change-backups\pr01-20260928-deploy\hermes_node.py' -Destination 'C:\CyberGene\HermesNode\hermes_node.py' -Force
```

Restart the Pablo process after this copy. Keep both bot service drop-ins and
the new environment file so every client continues to use the rotated key.

The prior code and config backups are recovery artifacts, not deployment
defaults. Historical credentials in the Git history require separate rotation.
