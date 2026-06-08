"""Hermes tools facade: legacy uyumluluk + moduler Hermes fonksiyonlari."""
from __future__ import annotations

import functools as _functools
import inspect as _inspect

from . import _legacy as _legacy


def _sync_legacy_globals() -> None:
    for _name, _value in globals().items():
        if _name.startswith("__") or _name in {"_legacy", "_sync_legacy_globals", "_sync_from_legacy_globals", "_wrap_legacy_function"}:
            continue
        _legacy.__dict__[_name] = _value


def _sync_from_legacy_globals() -> None:
    for _name, _value in _legacy.__dict__.items():
        if _name.startswith("__") or _inspect.isfunction(_value):
            continue
        globals()[_name] = _value


def _wrap_legacy_function(_func):
    @_functools.wraps(_func)
    def _wrapped(*args, **kwargs):
        _sync_legacy_globals()
        _result = _func(*args, **kwargs)
        _sync_from_legacy_globals()
        return _result
    return _wrapped


for _name, _value in list(_legacy.__dict__.items()):
    if _name.startswith("__"):
        continue
    globals()[_name] = _wrap_legacy_function(_value) if _inspect.isfunction(_value) else _value

from ._finans import hermes_finans_listele, hermes_finans_ekle, hermes_finans_sil
from ._musteri import hermes_musteri_listele, hermes_musteri_ekle, hermes_musteri_sil, hermes_musteri_guncelle
from ._saglik import hermes_saglik_raporu, hermes_watchdog_canli_kontrol
from ._vision import hermes_gorsel_analiz_plani, hermes_gorsel_dosya_incele, hermes_gorsel_analiz_istegi, hermes_gorsel_analiz_uygula, _vision_provider_config
from ._self import hermes_kalite_raporu
from ._code_intel import hermes_tool_hijyen_raporu, hermes_entegrasyon_degerlendirmesi, hermes_kod_yapisal_ara, hermes_kod_fonksiyon_bul

__all__ = [name for name in globals() if not name.startswith("__")]
