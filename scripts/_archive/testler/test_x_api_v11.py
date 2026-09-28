#!/usr/bin/env python3
"""
Test: X/Twitter API v1.1 — media/upload + statuses/update via OAuth 1.0a
Essential tier v1.1 write endpoints genelde açıktır.
"""
import os
import sys
from typing import Dict, Any

CRED_PATH: str = os.path.expanduser("/opt/hermes/.env.x")


def parse_env(filepath: str) -> Dict[str, str]:
    """Parse KEY=\"value\" env file."""
    result: Dict[str, str] = {}
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if "=" not in line or line.startswith("#"):
                    continue
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip().strip('"')
        return result
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)


def test_v1_1_post(creds: Dict[str, str]) -> None:
    """Test tweet posting via v1.1 API."""
    import requests
    from requests_oauthlib import OAuth1

    auth = OAuth1(
        creds["CONSUMER_KEY"],
        creds["CONSUMER_KEY_SECRET"],
        creds["ACCESS_TOKEN"],
        creds["ACCESS_TOKEN_SECRET"],
    )

    payload: Dict[str, str] = {
        "status": f"API test — v1.1 {__import__('datetime').datetime.now().isoformat()}"
    }

    try:
        resp: requests.Response = requests.post(
            "https://api.twitter.com/1.1/statuses/update.json",
            data=payload,
            auth=auth,
            timeout=15,
        )
        data: Dict[str, Any] = resp.json()

        if resp.status_code == 200:
            tweet_id: str = data.get("id_str", "unknown")
            print(f"  ✅ v1.1 tweet posted: {tweet_id}")

            # Sil
            del_resp: requests.Response = requests.post(
                f"https://api.twitter.com/1.1/statuses/destroy/{tweet_id}.json",
                auth=auth,
                timeout=10,
            )
            if del_resp.status_code == 200:
                print(f"  ✅ Test tweet deleted: {tweet_id}")
            else:
                print(f"  ⚠️ Delete failed: {del_resp.status_code}")
        else:
            print(f"  v1.1 hata: {resp.status_code} — {data.get('errors', data)}")
            sys.exit(1)

    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)


def main() -> None:
    print("=== X/Twitter API v1.1 Test ===")
    creds: Dict[str, str] = parse_env(CRED_PATH)
    test_v1_1_post(creds)
    print("\n✅ PASS: v1.1 posting works")


if __name__ == "__main__":
    main()
