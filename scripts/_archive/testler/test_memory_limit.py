#!/usr/bin/env python3
"""
Test: Memory limit config patch
Verifies that memory_char_limit and user_char_limit are readable from config.yaml
after patch is applied.
"""
import os
import sys
import yaml
from typing import Dict, Any

CONFIG_PATH = os.path.expanduser("~/.hermes/config.yaml")


def read_config() -> Dict[str, Any]:
    """Read and parse Hermes config.yaml."""
    try:
        with open(CONFIG_PATH, "r") as f:
            config: Dict[str, Any] = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"FAIL: Config not found at {CONFIG_PATH}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"FAIL: YAML parse error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: Unexpected error reading config: {e}")
        sys.exit(1)


def test_memory_limits(config: Dict[str, Any]) -> None:
    """Assert memory limits are at expected values."""
    memory: Dict[str, Any] = config.get("memory", {})
    assert isinstance(memory, dict), "memory config must be a dict"

    mem_limit: int = memory.get("memory_char_limit", 0)
    user_limit: int = memory.get("user_char_limit", 0)

    print(f"  memory_char_limit: {mem_limit}")
    print(f"  user_char_limit:   {user_limit}")

    assert mem_limit >= 16000, (
        f"FAIL: memory_char_limit={mem_limit}, expected >= 16000"
    )
    assert user_limit >= 4000, (
        f"FAIL: user_char_limit={user_limit}, expected >= 4000"
    )


def test_config_writeable(config: Dict[str, Any]) -> None:
    """Verify config file is writable (not read-only)."""
    mode: int = os.stat(CONFIG_PATH).st_mode
    owner_write: bool = bool(mode & 0o200)  # owner write bit
    if not owner_write:
        print("WARN: Config file is read-only for owner")
    else:
        print("  Config file is writable: OK")


def main() -> None:
    """Run all memory limit tests."""
    print("=== Memory Limit Config Test ===")
    config: Dict[str, Any] = read_config()
    test_memory_limits(config)
    test_config_writeable(config)
    print("\nPASS: All memory limit checks passed")


if __name__ == "__main__":
    main()
