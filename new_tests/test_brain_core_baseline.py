from pathlib import Path


def test_session_db_import():
    from hermes_state import SessionDB

    assert SessionDB is not None


def test_session_db_creation(tmp_path):
    from hermes_state import SessionDB

    db = SessionDB(db_path=tmp_path / "state.db")
    try:
        assert db.db_path == tmp_path / "state.db"
    finally:
        db.close()


def test_conversation_loop_import():
    from agent.conversation_loop import run_conversation

    assert callable(run_conversation)


def test_gateway_runner_import():
    from gateway.run import GatewayRunner

    assert GatewayRunner is not None
