def test_brain_public_facade_imports():
    from brain import (
        check_health,
        close_db,
        get_budget_left,
        get_db,
        get_metrics,
        get_session,
        track_usage,
    )

    assert callable(get_db)
    assert callable(get_session)
    assert callable(close_db)
    assert callable(check_health)
    assert callable(get_metrics)
    assert callable(track_usage)
    assert callable(get_budget_left)


def test_brain_health_shape():
    from brain import check_health

    health = check_health()

    assert health["status"] in {"ok", "degraded"}
    assert "timestamp" in health
    assert "memory" in health
    assert "gateway" in health


def test_brain_metrics_shape():
    from brain import get_metrics

    metrics = get_metrics()

    assert "active_sessions" in metrics
    assert "disk_usage" in metrics
