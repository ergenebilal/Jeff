#!/usr/bin/env python3
"""Hermes tools facade.

Eski `import tools` zincirini korur. Gerçek implementasyon `hermes_tools`
paketindedir; bu facade monkeypatch/setattr işlemlerini de oraya yansıtır.
"""

import sys
import types

import hermes_tools as _hermes_tools


def _refresh_exports() -> None:
    for _name in getattr(_hermes_tools, "__all__", []):
        globals()[_name] = getattr(_hermes_tools, _name)


class _ToolsFacade(types.ModuleType):
    def __getattr__(self, name):
        return getattr(_hermes_tools, name)

    def __setattr__(self, name, value):
        types.ModuleType.__setattr__(self, name, value)
        if not name.startswith("__"):
            setattr(_hermes_tools, name, value)

    def __delattr__(self, name):
        types.ModuleType.__delattr__(self, name)
        if hasattr(_hermes_tools, name):
            delattr(_hermes_tools, name)


_refresh_exports()
__all__ = [name for name in globals() if not name.startswith("__")]
sys.modules[__name__].__class__ = _ToolsFacade
