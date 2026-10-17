"""WebSocket decision.submit validation (events.yaml contract)."""

from typing import Any

from complibot.schemas import Finding

MIN_REASON_LEN = 10
DECISION_ACTIONS = frozenset({"accept", "reject", "edit", "escalate", "reopen", "override"})
OVERRIDE_ACTIONS = frozenset({"accept", "reject", "edit", "escalate"})
EDITABLE_FIELDS = ("title", "severity", "rationale", "remediation")


def decision_validation_error(
    action: str | None, payload: dict[str, Any], finding: Finding
) -> str | None:
    """Return a rejection code, or None if valid."""
    if action not in DECISION_ACTIONS:
        return "invalid"
    effective = action
    if action == "override":
        effective = payload.get("overrideAction")
        if effective not in OVERRIDE_ACTIONS:
            return "invalid"
    reason = payload.get("reason") or ""
    if not isinstance(reason, str):
        return "invalid"
    needs_reason = action in ("reject", "escalate", "reopen", "override") or effective in (
        "reject",
        "escalate",
    )
    if effective == "edit":
        edits = payload.get("edits")
        if not isinstance(edits, dict) or not edits:
            return "invalid"
        if set(edits) - set(EDITABLE_FIELDS):
            return "invalid"
        if "severity" in edits and edits["severity"] != finding.severity:
            needs_reason = True
    if needs_reason and len(reason.strip()) < MIN_REASON_LEN:
        return "invalid"
    if effective == "escalate" and not payload.get("assigneeId"):
        return "invalid"
    return None
