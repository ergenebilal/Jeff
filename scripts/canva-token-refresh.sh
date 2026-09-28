#!/bin/bash
# Canva token refresh — her 3 saatte bir çağrılır

TOKEN_FILE="/opt/canva-mcp-server/.canva_tokens.json"
ENV_FILE="/opt/canva-mcp-server/.env"

# Read current tokens
if [ ! -f "$TOKEN_FILE" ]; then
    echo "NO_TOKEN_FILE"
    exit 1
fi

CLIENT_ID=$(grep CANVA_CLIENT_ID "$ENV_FILE" | head -1 | cut -d= -f2)
CLIENT_SECRET=$(grep CANVA_CLIENT_SECRET "$ENV_FILE" | head -1 | cut -d= -f2)

# Exchange refresh token
RESPONSE=$(curl -s -X POST "https://api.canva.com/rest/v1/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "refresh_token=$(python3 -c "import json; print(json.load(open('$TOKEN_FILE'))['refresh_token'])")")

echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'access_token' in data:
        with open('$TOKEN_FILE', 'w') as f:
            json.dump(data, f, indent=2)
        # Update .env
        with open('$ENV_FILE') as f:
            env = f.read()
        lines = env.split('\n')
        new_lines = []
        for line in lines:
            if line.startswith('CANVA_ACCESS_TOKEN='):
                new_lines.append(f'CANVA_ACCESS_TOKEN={data[\"access_token\"]}')
            elif line.startswith('CANVA_REFRESH_TOKEN='):
                new_lines.append(f'CANVA_REFRESH_TOKEN={data[\"refresh_token\"]}')
            else:
                new_lines.append(line)
        with open('$ENV_FILE', 'w') as f:
            f.write('\n'.join(new_lines))
        print(f'OK: refreshed, expires_in={data[\"expires_in\"]}s')
    else:
        print(f'FAIL: {data.get(\"error\", \"unknown\")}')
except Exception as e:
    print(f'FAIL: {e}')
"