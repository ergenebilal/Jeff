"""Phase 12 testleri."""

from jeff_cognitive.autonomy import check


def test_read_allowed():
    assert check("READ")["decision"] == "ALLOW"


def test_irreversible_needs_approval():
    r = check("IRREVERSIBLE_ACTION")
    assert r["decision"] == "APPROVAL_REQUIRED" and r["approval"] == "critical"


def test_no_bypass():
    # onay verilmis olsa bile governance kapaliysa DENY
    r = check("LOW_RISK_ACT", governance_ok=False, approval_granted=True)
    assert r["decision"] == "DENY"


def test_approval_unlocks():
    r = check("EXTERNAL_COMMUNICATION", governance_ok=True, approval_granted=True)
    assert r["decision"] == "ALLOW"


def test_unknown_category_denied():
    assert check("NUKE")["decision"] == "DENY"
