#!/usr/bin/env python3
"""Write N8N API key from command line argument to .env"""
import sys, os

env_path = "/opt/hermes/.env"

if len(sys.argv) > 1:
    key = sys.argv[1]
else:
    print("Usage: set_n8n_key.py <JWT_TOKEN>")
    sys.exit(1)

with open(env_path) as f:
    lines = f.read().splitlines()

not_line = "N8N_API_KEY=NOT_SET_YET"
found = False
for i, line in enumerate(lines):
    if line.startswith("N8N_API_KEY="):
        lines[i] = "N8N_API_KEY=" + key
        found = True
        break

if not found:
    lines.append("N8N_API_KEY=" + key)

with open(env_path, "w") as f:
    f.write("\n".join(lines) + "\n")

# Verify
for line in open(env_path):
    if line.startswith("N8N_API_KEY="):
        k = line.strip().split("=", 1)[1]
        print("OK: key length=%d chars" % len(k))
        print("Starts with: " + k[:20])
        print("Ends with: " + k[-20:])
        break
