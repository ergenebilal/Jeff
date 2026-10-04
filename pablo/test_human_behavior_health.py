"""Health contract only: no Windows imports or desktop effects."""
import ast
from pathlib import Path
from types import SimpleNamespace


def health(engine):
    tree=ast.parse(Path(__file__).with_name('hermes_node.py').read_text(encoding='utf-8'))
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='human_behavior_snapshot')
    module=ast.Module(body=[function],type_ignores=[])
    scope={'_human_behavior':engine,'HUMAN_BEHAVIOR_SOURCE_SHA256':'a'*64}
    exec(compile(module,'health-contract','exec'),scope)
    return scope['human_behavior_snapshot']()


def test_unloaded_module_not_verified_disabled():
    result=health(None);assert not result['known'] and not result['disabled_verified']


def test_loaded_fast_modes_verified_without_actions():
    calls=[]
    def mode(target):calls.append(target);return 'FAST'
    result=health(SimpleNamespace(get_mode=mode))
    assert result['known'] and result['disabled_verified'] and len(calls)==4
    assert result['loaded_private_source_sha256']=='a'*64


def test_one_stealth_mode_fails_disable_acceptance():
    result=health(SimpleNamespace(get_mode=lambda target:'STEALTH' if target=='instagram.com' else 'FAST'))
    assert result['known'] and not result['disabled_verified']


def test_mode_failure_never_passes_or_leaks_exception_text():
    def broken(target):raise ValueError('private fixture')
    result=health(SimpleNamespace(get_mode=broken))
    assert not result['known'] and not result['disabled_verified'] and result['reason']=='ValueError'
    assert 'private fixture' not in str(result)
