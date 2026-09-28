# System Verification Workflow

Comprehensive health check after maintenance or changes. Run all checks, interpret as a set.

## Checklist

### 1. Gateway
```bash
curl -s http://127.0.0.1:9119/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print('Version:', d.get('version','N/A'))"
```
Pass: version number returned. Fail: gateway down or API unreachable.

### 2. MissingSessionID
```bash
grep -r 'MissingSessionID' /opt/hermes/logs/ /home/hermes/logs/ 2>/dev/null | grep "$(date +%Y-%m-%d)" | tail -5
```
Pass: empty. Fail: errors present.

### 3. Fallback Model
```bash
python3 -c "import yaml; c=yaml.safe_load(open('/home/hermes/.hermes/config.yaml')); print('Fallback:', c.get('fallback_model','N/A'))"
```
Pass: configured model returned. Fail: missing or invalid.

### 4. Goals DB
```bash
python3 -c "import sqlite3; c=sqlite3.connect('/home/hermes/.hermes/goals.db').cursor(); c.execute('SELECT status,COUNT(*) FROM goals GROUP BY STATUS'); print(dict(c.fetchall()))"
```
Pass: goals exist. Fail: missing or empty.

### 5. Plugins/Tools
```bash
python3 -c "import sys; sys.path.insert(0,'/home/hermes/.hermes/hermes-agent'); from tools.registry import discover_builtin_tools; print(f'Tools: {len(discover_builtin_tools())}')"
```
Pass: tools discovered. Fail: import error.

### 6. MCP Trust
```bash
grep -r 'unrecognized trust' /opt/hermes/logs/ 2>/dev/null | tail -3
```
Pass: empty. Fail: warnings present.

### 7. Logrotate Cron
```bash
crontab -l | grep -i logrotate
```
Pass: job present. Fail: missing.

### 8. Backup State
```bash
ls ~/backups/state-*.db 2>/dev/null | tail -1
tail -3 /opt/backups/logs/cron.log 2>/dev/null
```
Pass: snapshot exists + log shows success. Fail: missing or failed.

### 9. Drive Upload
```bash
rclone ls gdrive:Jeff-Backup/ --config /home/hermes/.config/rclone/rclone.conf 2>/dev/null | tail -3
```
Pass: recent files. Fail: empty or connection error.

### 10. Model/Provider
```bash
python3 -c "import yaml; c=yaml.safe_load(open('/home/hermes/.hermes/config.yaml')); print('Model:', c.get('model','N/A')); print('Provider:', c.get('provider','N/A'))"
```
Pass: configured. Fail: missing.

## Interpretation
- All green → healthy, no action.
- Some failures → investigate specifics, prioritize critical (gateway, backup).
- All failures → system-wide issue, check connectivity and gateway process.

## Pitfalls
- MissingSessionID grep returns empty even when errors exist in journal (not in log files) → check `journalctl -u hermes-gateway` as alternative.
- Goals DB may show in_progress entries from current session — these are normal, not failures.
- Plugin/tool count varies by model provider — compare against previous known-good count, not absolute number.
- Drive upload may show old files if cron hasn't run recently — check cron.log timestamp, not file dates.
