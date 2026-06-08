# Chapter 8: Production Deployment

## Concept

Development is easy. Production is hard. This chapter covers making your agent stack survive server reboots, handle SSL, and run securely.

## Docker Compose — One Command to Rule All

Create a `docker-compose.yml` that deploys your entire stack:

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
    environment:
      - N8N_SECURE_COOKIE=false
      - WEBHOOK_URL=https://n8n.yourdomain.com

  postgres:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    volumes:
      - pg_data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: hermes
      POSTGRES_PASSWORD: ${PG_PASSWORD}
      POSTGRES_DB: hermes

  ollama:
    image: ollama/ollama:latest
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  n8n_data:
  pg_data:
  ollama_data:
```

Deploy with:

```bash
docker compose up -d
```

## SSL with Traefik (Reverse Proxy)

```yaml
# In your docker-compose.yml
services:
  traefik:
    image: traefik:v3.0
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - traefik_data:/etc/traefik
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`traefik.yourdomain.com`)"
      - "traefik.http.routers.dashboard.service=api@internal"
```

Traefik auto-generates SSL certificates via Let's Encrypt. No manual certbot.

## Security Checklist

- [x] SSH key-only login (no passwords)
- [x] UFW firewall (allow ports 22, 80, 443 only)
- [x] Fail2ban for SSH
- [x] n8n behind authentication (or VPN-only)
- [x] Database passwords in .env (not config files)
- [x] Regular backups (cron job)
- [x] Docker containers run as non-root users
- [x] Hermes API key stored in secure env
- [x] Agent has safety rails (no rm -rf, no spending)

## Backup Strategy

```bash
#!/bin/bash
# /opt/backup.sh — run daily via cron
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/backups/$DATE"

mkdir -p $BACKUP_DIR

# Backup n8n workflows
docker exec n8n n8n export:workflow --all --output=/tmp/n8n-backup.json
docker cp n8n:/tmp/n8n-backup.json $BACKUP_DIR/

# Backup PostgreSQL
pg_dump -h localhost -U hermes hermes > $BACKUP_DIR/hermes-db.sql

# Backup Hermes config
cp -r ~/.hermes $BACKUP_DIR/hermes-config

# Upload to remote (optional)
# rclone sync $BACKUP_DIR remote:backups/

echo "Backup complete: $BACKUP_DIR"
```

## Survival Checklist

After a server reboot, verify:

```bash
# 1. Docker containers are running
docker ps | grep -E "n8n|postgres|ollama|traefik"

# 2. Hermes is responding
hermes run "Are you alive?"

# 3. n8n workflows are active
curl -s https://n8n.yourdomain.com/healthz

# 4. Database is accessible
psql -h localhost -U hermes -d hermes -c "SELECT 1"

# 5. Telegram notifications work (send test message)
```

## Pro Tips

1. **Use .env files** for secrets. Never commit them.
2. **Pin Docker image versions** (`n8nio/n8n:2.22.2` not `:latest`)
3. **Monitor disk** with a simple cron: `df -h | grep /dev/sda`
4. **Test recovery** — actually reboot your server and verify everything comes back up

## Next Steps

Your stack is production-ready. Chapter 9 covers scaling — handling multiple clients, separating concerns, and managing costs.
