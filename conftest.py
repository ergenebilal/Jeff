"""Ensure local project root is first in sys.path for all tests.

Some tests import from the installed hermes-agent (e.g., tools, agent packages),
which can shadow local modules like mini_swe_runner.  This conftest ensures
the project root is always searched first.
"""

import sys
from pathlib import Path


_PROJECT_ROOT = str(Path(__file__).resolve().parent)


def _ensure_project_root():
    if _PROJECT_ROOT in sys.path:
        sys.path.remove(_PROJECT_ROOT)
    sys.path.insert(0, _PROJECT_ROOT)


_ensure_project_root()


def pytest_load_initial_conftests():
    _ensure_project_root()
