# Gateway Health Troubleshooting

When the Hermes Gateway health endpoint (`/health`) times out but the service shows as active:

1. **Check logs for blocking**
   ```bash
   journalctl -u hermes-gateway -n 100 --no-pager
   ```
   Look for repeated warnings about tool checks failing (e.g., `_browser_cdp_check`, `_check_kanban_mode`) – these can cause the gateway to stall while still accepting TCP connections.

2. **Restart the gateway**
   ```bash
   sudo systemctl restart hermes-gateway
   ```
   After restart, re‑test the health endpoint:
   ```bash
   curl -s http://localhost:8642/health
   ```

3. **Verify MCP workers**
   The gateway spawns many MCP subprocesses (n8n, Google Workspace, etc.). If one hangs, it can block the main event loop.
   - List MCP processes: `ps -ef | grep mcp`
   - Kill any stuck MCP and let the gateway respawn it.

4. **Preventive**
   - Keep the `gateway-child-sentinel.sh` cron active (runs every 5 min to clean zombie child processes).
   - Ensure `persistent_shell: false` in config.yaml to avoid shell accumulation.

If the problem persists after a restart, check for a `--replace`/`drop_pending_updates=True` loop in the Telegram bot (see the `system-durumu` skill’s “İKİNCİ KÖK SEBEP” section).