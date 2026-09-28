#!/usr/bin/env python3
"""
Test: X/Twitter API v2 credentials are valid for posting.
Sends a minimal test tweet via OAuth 1.0a using requests_oauthlib.
"""
import os
import sys
from typing import Dict, Optional, Any

# Type hint + try-except (protokol madde 3)
CONFIG_PATH: str = os.path.expanduser("/opt/hermes/.env.x")


def parse_env(filepath: str) -> Dict[str, str]:
    """Parse KEY=\"value\" env file into dict."""
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
    except FileNotFoundError:
        print(f"FAIL: Credentials file not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: Error reading {filepath}: {e}")
        sys.exit(1)


def test_credentials_loaded(creds: Dict[str, str]) -> bool:
    """Verify all 4 OAuth 1.0a credentials are present."""
    required: list[str] = ["CONSUMER_KEY", "CONSUMER_KEY_SECRET", "ACCESS_TOKEN", "ACCESS_TOKEN_SECRET"]
    for key in required:
        if not creds.get(key):
            print(f"FAIL: Missing credential: {key}")
            print(f"  Mevcut anahtarlar: {list(creds.keys())}")
            return False
        val: str = creds[key]
        print(f"  ✅ {key}: ...{val[-4:]}")
    return True


def test_tweet_post(creds: Dict[str, str]) -> None:
    """Send a test tweet to verify API v2 write access."""
    import requests
    from requests_oauthlib import OAuth1

    auth = OAuth1(
        creds["CONSUMER_KEY"],
        creds["CONSUMER_KEY_SECRET"],
        creds["ACCESS_TOKEN"],
        creds["ACCESS_TOKEN_SECRET"],
    )

    payload: Dict[str, str] = {"text": f"🤖 API test tweet — {__import__('datetime').datetime.now().isoformat()}"}

    try:
        resp: requests.Response = requests.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
            auth=auth,
            timeout=15,
        )
        data: Dict[str, Any] = resp.json()

        if resp.status_code == 201:
            tweet_id: str = data.get("data", {}).get("id", "unknown")
            print(f"  ✅ Tweet posted: {tweet_id}")
            # Delete test tweet
            del_resp: requests.Response = requests.delete(
                f"https://api.twitter.com/2/tweets/{tweet_id}",
                auth=auth,
                timeout=10,
            )
            if del_resp.status_code == 200:
                print(f"  ✅ Test tweet deleted: {tweet_id}")
            else:
                print(f"  ⚠️ Could not delete test tweet: {del_resp.status_code}")
        else:
            print(f"FAIL: API returned {resp.status_code}")
            print(f"  Yanıt: {data}")
            print(f"  Bu session'da tweet atma yetkisi yok. Essential tier kontrol et.")
            sys.exit(1)

    except requests.exceptions.Timeout:
        print("FAIL: Twitter API timeout")
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)


def main() -> None:
    """Run X API credential and posting test."""
    print("=== X/Twitter API Test ===")
    creds: Dict[str, str] = parse_env(CONFIG_PATH)
    if not test_credentials_loaded(creds):
        sys.exit(1)
    test_tweet_post(creds)
    print("\n✅ PASS: X API v2 credentials valid, posting works")


if __name__ == "__main__":
    main()
