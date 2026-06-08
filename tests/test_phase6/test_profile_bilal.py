"""Tests for Phase 6 profile_bilal module."""

from brain.phase6.profile_bilal import build_profile, domain_recommendations


def test_build_profile_no_data():
    profile = build_profile()
    assert profile["total_sessions"] == 0
    assert "recommendations" in profile


def test_domain_recommendations():
    result = domain_recommendations()
    assert "available_domains" in result
    assert "current_profile" in result
    assert len(result["available_domains"]) == 3

    domain_names = [d["domain"] for d in result["available_domains"]]
    assert "klinik" in domain_names
    assert "restoran" in domain_names
    assert "ergeneai" in domain_names
