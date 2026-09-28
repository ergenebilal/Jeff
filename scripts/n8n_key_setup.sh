#!/usr/bin/env bash
# Write n8n API key to .env — full JWT

KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3ODZmMDMxMC1jZDUwLTRhNmEtOTdhMC1hYzUxZjg0MjkzOGIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiOGQ1ZmMwYjMtZmI0Yy00YmI5LWFhMzYtZTliMDhhMTczZmU1IiwiaWF0IjoxNzgxMDk5NjQwfQ.BvmH2ompuDjW1v53mQzUcSJUElAWdOR9q4wRjuTkhj0"

sed -i '/^N8N_API_KEY=*** /opt/hermes/.env
echo "N8N_API_KEY=*** >> /opt/hermes/.env

echo "✅ N8N API key written to .env"
echo "Key length: ${#KEY} chars"
head -3 /opt/hermes/.env | grep N8N_API || echo "Done"
