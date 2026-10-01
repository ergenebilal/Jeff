# Versioned cognitive baseline

Captured Python sources and tests from `/home/hermes/jeff_cognitive` on
2026-10-01. The original byte hashes and external source hashes are recorded in
`docs/cognitive-source-origin.json`; the repository version is pinned by
`docs/cognitive-source-current.json`. Runtime databases, lessons, private memory,
configuration, logs and backup copies are excluded.

Run from the repository root:

```sh
python -m pip install 'pytest>=8,<10'
python -m pytest -q jeff_cognitive/tests
python scripts/cognitive_inventory.py --compare docs/cognitive-source-current.json
```

The internal core uses the Python standard library. Original SQLite helpers
committed transactions without closing connections, leaving database handles
open. Four stores now close on every successful or failed operation. Tests also
restore the environment and disable live worker/Board imports by default.

Portable baseline: 104 passed, 11 skipped. The skipped tests require external
ADE/Board/WorkerPool sources from `/opt/hermes/jeff_v2`. Their 171 source hashes
are recorded but those sources are not bundled here. Live dependency tests need
`JEFF_COGNITIVE_LIVE_TESTS=1` in an **isolated** installation; they can write
external Board/ADE state. This is not proof that the complete production
cognitive stack can be reconstructed from this repository alone.

This snapshot and the connection fixes do not change the running Hermes
cognitive hook. Activate a source revision only after validating its external
dependencies and loaded hook configuration. The older Claude phase branch is
not merged by this import.
