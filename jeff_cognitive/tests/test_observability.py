"""Phase 14 testleri."""

import tempfile
from pathlib import Path

from jeff_cognitive import CognitiveLoop, CognitiveStore
from jeff_cognitive.observability import export_log, reconstruct


def test_reconstruct_answers_all():
    with tempfile.TemporaryDirectory() as tmp:
        store = CognitiveStore(Path(tmp) / "c.db")
        loop = CognitiveLoop(store)
        s = store.create(objective="X", session_id="s")
        s.assumptions.append("a1")
        s.unknowns.append("u1")
        store.save(s)
        loop.run(s.goal_id, max_steps=20)
        rep = reconstruct(store, s.goal_id)
        for key in ("why", "beliefs", "evidence", "unknowns", "decisions",
                    "actions", "reality", "verification", "lessons", "changes"):
            assert key in rep
        assert rep["why"] == "X"
        assert len(export_log(store, s.goal_id)) == 10
