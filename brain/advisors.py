"""Proposal advisor: inspect past decisions before recommending."""

from __future__ import annotations

from typing import Any


def assess_proposal(proposal: str, task: str = "") -> dict[str, Any]:
    return {
        "similar_count": 0,
        "success_rate": None,
        "warning": "",
        "notes": [f"Proposal: {str(proposal)[:120]}", f"Task: {str(task)[:120]}"],
    }


def format_assessment(assessment: dict[str, Any]) -> str:
    warning = assessment.get("warning") or "Benzer riskli karar bulunmadi."
    return str(warning)
