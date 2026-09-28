#!/usr/bin/env python3
"""Decrypt n8n credentials — OpenSSL EVP format."""
import sys, json, base64, sqlite3
from hashlib import md5
from Crypto.Cipher import AES

def evp_kdf(key: bytes, salt: bytes, key_size=32, iv_size=16):
    """OpenSSL EVP_BytesToKey with MD5."""
    derived = b""
    data = b""
    while len(derived) < key_size + iv_size:
        data = md5(data + key + salt).digest()
        derived += data
    return derived[:key_size], derived[key_size:key_size+iv_size]

def decrypt_openssl(encrypted_b64: str, password: str) -> dict:
    """Decrypt OpenSSL-compatible encrypted data."""
    raw = base64.b64decode(encrypted_b64)
    if raw[:8] != b"Salted__":
        raise ValueError("Not salted OpenSSL format")
    salt = raw[8:16]
    ct = raw[16:]

    aes_key, iv = evp_kdf(password.encode(), salt)
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(ct)

    # Remove PKCS7 padding
    pad_len = decrypted[-1]
    if 0 < pad_len <= 16:
        decrypted = decrypted[:-pad_len]

    return json.loads(decrypted.decode("utf-8"))

# --- Main ---
db_path = "/tmp/n8n-db.sqlite"
enc_key = "pDOhFPb6+jIVKaiZrRA8YGzuECZ2Y2tI"

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT id, name, type, data FROM credentials_entity ORDER BY type")
rows = cur.fetchall()

data_field = rows[0][3]
print(f"First row data length: {len(data_field)}")
print(f"First 30 chars: {data_field[:30]}")
print(f"Starts with U2FsdGVkX1: {data_field.startswith('U2FsdGVkX1')}")
print(f"Starts with Salted__ in base64: {base64.b64decode(data_field[:12])[:8]}")

output = {}
for cid, name, ctype, data_raw in rows:
    print(f"\n🔑 {name} ({ctype})")
    try:
        decrypted = decrypt_openssl(data_raw, enc_key)
        print(f"   ✅ Decrypted OK")
        for k, v in decrypted.items():
            if isinstance(v, str) and len(v) > 6:
                print(f"     {k}: {v[:6]}...{v[-4:]} ({len(v)} chars)")
            else:
                print(f"     {k}: {v}")
        output[name] = {"type": ctype, "data": decrypted}
    except Exception as e:
        print(f"   ❌ {e}")

conn.close()

out_path = "/tmp/n8n-credentials.json"
with open(out_path, "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(f"\n✅ {len(output)}/{len(rows)} decrypted to {out_path}")
