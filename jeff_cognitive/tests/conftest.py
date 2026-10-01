"""Portable baseline never imports live workers or writes production state.

Explicit live tests need JEFF_COGNITIVE_LIVE_TESTS=1 in an isolated installation.
They may write Board/ADE state and must not be run against production.
"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _isolated_hermes_home(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("hermes-home")
    previous = os.environ.get("HERMES_HOME")
    os.environ["HERMES_HOME"] = str(tmp)
    from jeff_cognitive import runtime_bridge, ade
    original = runtime_bridge.live_import
    board_candidates = ade._BOARD_CANDIDATES
    if os.environ.get('JEFF_COGNITIVE_LIVE_TESTS') != '1':
        def unavailable(name):
            raise runtime_bridge.BridgeUnavailable('Live dependency disabled in portable baseline')
        runtime_bridge.live_import = unavailable
        ade._BOARD_CANDIDATES = []
    try:
        yield tmp
    finally:
        runtime_bridge.live_import = original
        ade._BOARD_CANDIDATES = board_candidates
        if previous is None:
            os.environ.pop('HERMES_HOME', None)
        else:
            os.environ['HERMES_HOME'] = previous
