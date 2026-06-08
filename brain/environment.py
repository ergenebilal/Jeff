"""Environment-aware path resolution for Hermes.

Resolves paths correctly across:
  - Local Windows development (C:/Users/...)
  - Production Linux (/opt/hermes/, /home/hermes/)
"""

import os
import platform
import socket
from pathlib import Path
from typing import Optional


class Environment:
    """Detect and resolve environment-dependent paths."""

    _instance = None
    _is_production: Optional[bool] = None
    _hermes_home: Optional[Path] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._detect()
        return cls._instance

    def _detect(self):
        """Detect environment type."""
        system = platform.system().lower()

        # Production check: Linux + hostname contains 'hermes' or path exists
        if system == "linux":
            if Path("/opt/hermes").exists():
                self._is_production = True
                self._hermes_home = Path("/opt/hermes")
            elif Path("/home/hermes").exists():
                self._is_production = True
                self._hermes_home = Path("/home/hermes")
            else:
                self._is_production = False
                self._hermes_home = Path.home() / ".hermes"
        else:
            # Windows, macOS, etc. — always development
            self._is_production = False
            self._hermes_home = Path.home() / ".hermes"

    @property
    def is_production(self) -> bool:
        return self._is_production

    @property
    def is_windows(self) -> bool:
        return platform.system().lower() == "windows"

    @property
    def hermes_home(self) -> Path:
        return self._hermes_home

    def resolve(self, *parts: str) -> Path:
        """Resolve a path relative to hermes home.

        Example:
            env.resolve("hq", "index.html") -> /opt/hermes/hq/index.html (prod)
                                            -> ~/.hermes/hq/index.html (dev)
        """
        return self._hermes_home.joinpath(*parts)

    def resolve_abs(self, path: str) -> Path:
        """Resolve an absolute path that may differ between environments.

        Known mappings:
            /opt/hermes/...  -> local workspace equivalent
            /home/hermes/... -> local workspace equivalent
        """
        p = Path(path)
        p_str = str(p).replace("\\", "/")

        # Production paths that need local mapping
        if not p.exists():
            mappings = {
                "/opt/hermes": self._get_workspace_root(),
                "/home/hermes": Path.home(),
            }
            for prod_prefix, local_prefix in mappings.items():
                if p_str.startswith(prod_prefix):
                    rel = p_str[len(prod_prefix):].lstrip("/")
                    candidate = local_prefix / rel
                    if candidate.exists():
                        return candidate

        return p

    def _get_workspace_root(self) -> Path:
        """Return the local development workspace root."""
        # Try common locations
        candidates = [
            Path(os.environ.get("HERMES_WORKSPACE", "")),
            Path("C:/Users/lenovo/Documents/ClaudeProjects/workflows/_remote_opt_hermes"),
            Path.cwd(),
        ]
        for c in candidates:
            if c.exists() and (c / "mini_swe_runner.py").exists():
                return c
        return Path.cwd()

    @staticmethod
    def get() -> "Environment":
        """Get the singleton Environment instance."""
        return Environment()


# ── Convenience ──────────────────────────────────────────────────────────────

_env = Environment()


def hermes_home() -> Path:
    return _env.hermes_home


def is_production() -> bool:
    return _env.is_production


def resolve_path(path: str) -> Path:
    return _env.resolve_abs(path)
