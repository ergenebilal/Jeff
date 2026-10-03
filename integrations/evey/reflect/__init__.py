"""One critique call. Unavailable or malformed evaluations never pass.

The caller revises the output; this handler does not implement a correction loop.
The configured model route determines availability and cost.
"""

import json
import os
import hashlib
import re
from datetime import datetime, timezone

import importlib.util as _iu, os as _os
_spec = _iu.spec_from_file_location("evey_utils", _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "evey_utils.py"))
_eu = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_eu)
call_llm = _eu.call_llm

CRITIQUE_MODEL = "qwen35-4b"

SCHEMA = {
    "name": "reflect_on_output",
    "description": (
        "Evaluate your output before sending it. Pass your draft response "
        "and the original task. The tool will critique it using a cheap model "
        "and suggest improvements. Use this for important outputs: research "
        "summaries, daily reports, delegation results, goal reviews. "
        "Returns: evaluation status and critique notes; the caller revises the draft."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The original task or question",
            },
            "draft": {
                "type": "string",
                "description": "Your draft response to critique",
            },
            "criteria": {
                "type": "string",
                "description": "What to check for (e.g., 'accuracy, completeness, actionability')",
            },
        },
        "required": ["task", "draft"],
    },
}

CRITIQUE_PROMPT = """You are a quality reviewer. Critique this draft response.

ORIGINAL TASK: {task}

DRAFT RESPONSE: {draft}

CRITERIA: {criteria}

Review for:
1. Factual accuracy — are claims verifiable?
2. Completeness — does it answer the full question?
3. Actionability — can the reader act on this?
4. Conciseness — any unnecessary fluff?

If the draft is GOOD (score >= 7/10), respond with: PASS: [brief note]
If it needs improvement, respond with: FIX: [specific issues to fix]

Keep your critique under 100 words."""


def _critique(prompt):
    return call_llm(CRITIQUE_MODEL, prompt, max_tokens=200, temperature=0.3)


def handler(args, **kwargs):
    draft = args.get("draft", "") if isinstance(args, dict) else ""
    result = {
        "status": "needs_review", "reason_code": "invalid_input",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "draft_sha256": hashlib.sha256(draft.encode("utf-8")).hexdigest() if isinstance(draft, str) else None,
        "original_draft": draft, "suggestion": "Evaluation is incomplete; review before sending.",
    }
    try:
        if not isinstance(args, dict) or not isinstance(draft, str) or not draft.strip():
            return json.dumps(result)
        task = args.get("task", "")
        criteria = args.get("criteria", "accuracy, completeness, actionability")
        if not isinstance(task, str) or not task.strip() or len(draft) > 30000:
            return json.dumps(result)
        prompt = CRITIQUE_PROMPT.format(task=task, draft=draft, criteria=criteria)
        critique = _critique(prompt)
        if critique is None or (isinstance(critique, str) and not critique.strip()):
            result.update(status="unavailable", reason_code="empty_model_response")
        elif not isinstance(critique, str):
            result.update(reason_code="invalid_model_response")
        else:
            text = critique.strip()
            match = re.fullmatch(r"(PASS|FIX):[ \t]+([^\n]+)", text)
            if not match or re.search(r"\b(unavailable|not evaluated|could not evaluate|critique failed)\b", text, re.I):
                result.update(reason_code="invalid_verdict", critique=text)
            else:
                passed = match.group(1) == "PASS"
                result.update(status="pass" if passed else "needs_improvement",
                              reason_code="valid_critique", critique=text,
                              suggestion="Critique passed; this is not independent fact verification." if passed else
                              "Revise using the critique before sending.")
    except Exception as exc:
        result.update(status="unavailable", reason_code="model_exception", error_type=type(exc).__name__)
    return json.dumps(result)


def register(ctx):
    ctx.register_tool(
        name="reflect_on_output",
        toolset="evey_reflect",
        schema=SCHEMA,
        handler=handler,
    )
