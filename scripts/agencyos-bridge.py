#!/usr/bin/env python3
"""
AgencyOS MCP Bridge — stdio → HTTP JSON-RPC proxy
Hermes'e native MCP tool'u olarak bağlanır.
Token: ~/.hermes/agencyos-token dosyasından okunur.
"""
import json, sys, urllib.request, urllib.error, os

AGENCYOS_URL = "https://agencyos-app-88990.netlify.app/mcp"
TOKEN_FILE = os.path.expanduser("~/.hermes/agencyos-token")

def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    # Fallback: environment variable
    return os.environ.get("AGENCYOS_TOKEN", "")

def send_jsonrpc(method, params=None):
    token = get_token()
    body = {"jsonrpc": "2.0", "id": "h1", "method": method}
    if params is not None:
        body["params"] = params
    
    req = urllib.request.Request(
        AGENCYOS_URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": {"code": e.code, "message": e.read().decode()[:500]}}
    except Exception as e:
        return {"error": {"code": -1, "message": str(e)}}

def main():
    # Initialize handshake
    init_resp = send_jsonrpc("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "hermes", "version": "1.0"}
    })
    
    if "error" in init_resp:
        sys.stderr.write(f"INIT ERROR: {init_resp['error']}\n")
        sys.exit(1)
    
    # Tool listesini cache'le
    tools_resp = send_jsonrpc("tools/list", {})

    # NOT: notifications/initialized GONDERILMEZ. MCP spec'e gore bu bildirim
    # sadece client->server yonludur; server'in gondermesi tum client
    # surumlerinde validation hatasi uretir (2026-09: gunde ~800 uyari).
    # Gateway zaten kendi handshake'ini yapiyor.
    
    # Ana döngü
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        method = req.get("method", "")
        req_id = req.get("id")
        params = req.get("params", {})

        # JSON-RPC: id'siz mesajlar bildirimdir, ASLA cevap yazılmaz.
        # Ozellikle notifications/initialized yutulur: upstream'e forward
        # edilirse eski AgencyOS "-32601 Unknown method" doner ve id=null
        # cevabi gateway parser'ini patlatir (2026-09 gunde ~800 hata).
        if req_id is None:
            continue

        if method == "tools/list":
            result = tools_resp
        elif method == "resources/list":
            result = {"result": {"resources": []}}
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            result = send_jsonrpc("tools/call", {"name": tool_name, "arguments": tool_args})
        else:
            result = send_jsonrpc(method, params)
        
        response = {"jsonrpc": "2.0", "id": req_id}
        if "error" in result:
            response["error"] = result["error"]
        else:
            response["result"] = result.get("result", result)
        
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
