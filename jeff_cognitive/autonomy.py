"""Phase 12: Autonomy — ozerklik = sinirli yetki. Governance bypass YOK.

Kategoriler: READ < ANALYZE < PROPOSE < SIMULATE < LOW_RISK_ACT <
EXTERNAL_COMM < IRREVERSIBLE. Yuksek risk = guclu kontrol (onay sart).
"""

from __future__ import annotations

from typing import Any, Dict

CAT_READ = "READ"
CAT_ANALYZE = "ANALYZE"
CAT_PROPOSE = "PROPOSE"
CAT_SIMULATE = "SIMULATE"
CAT_LOW_RISK = "LOW_RISK_ACT"
CAT_EXTERNAL = "EXTERNAL_COMMUNICATION"
CAT_IRREVERSIBLE = "IRREVERSIBLE_ACTION"

CATEGORIES = (CAT_READ, CAT_ANALYZE, CAT_PROPOSE, CAT_SIMULATE,
              CAT_LOW_RISK, CAT_EXTERNAL, CAT_IRREVERSIBLE)

# kategori → (otomatik izin?, onay seviyesi)
_POLICY: Dict[str, Dict[str, Any]] = {
    CAT_READ: {"auto": True, "approval": "none"},
    CAT_ANALYZE: {"auto": True, "approval": "none"},
    CAT_PROPOSE: {"auto": True, "approval": "none"},
    CAT_SIMULATE: {"auto": True, "approval": "none"},
    CAT_LOW_RISK: {"auto": True, "approval": "low"},
    CAT_EXTERNAL: {"auto": False, "approval": "high"},
    CAT_IRREVERSIBLE: {"auto": False, "approval": "critical"},
}

DECISION_ALLOW = "ALLOW"
DECISION_APPROVAL = "APPROVAL_REQUIRED"
DECISION_DENY = "DENY"


def check(category: str, governance_ok: bool = True,
          approval_granted: bool = False) -> Dict[str, Any]:
    if category not in _POLICY:
        return {"decision": DECISION_DENY, "reason": f"bilinmeyen kategori: {category}"}
    pol = _POLICY[category]
    if not governance_ok:
        # Cognitive Core karari faydali olsa bile kapiyi ACAMAZ
        return {"decision": DECISION_DENY, "reason": "governance kapali — bypass yok",
                "approval": pol["approval"]}
    if pol["auto"] and pol["approval"] == "none":
        return {"decision": DECISION_ALLOW, "reason": "dusuk risk", "approval": "none"}
    if approval_granted:
        return {"decision": DECISION_ALLOW, "reason": "onay verildi",
                "approval": pol["approval"]}
    return {"decision": DECISION_APPROVAL, "reason": f"{pol['approval']} onay sart",
            "approval": pol["approval"]}
