#!/usr/bin/env python3
"""Write n8n API key to .env — usage: python3 write_n8n_key.py TOKEN"""
import sys, os

env_path = "/opt/hermes/.env"
key = sys.argv[1] if len(sys.argv) > 1 else input("N8N API Key: ").strip()

with open(env_path) as f:
    lines = f.read().splitlines()

found = False
for i, line in enumerate(lines):
    if line.startswith("N8N_API_KEY="):
        lines[i] = f"N8N_API_KEY={key}"
        found = True
        break
if not found:
    lines.append(f"N8N_API_KEY={key}")
with open(env_path, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"✅ N8N_API_KEY written ({len(key)} chars)")
