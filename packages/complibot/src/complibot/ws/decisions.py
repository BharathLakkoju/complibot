"""WebSocket decision.submit validation (events.yaml contract)."""

from typing import Any

from complibot.schemas import Finding

MIN_REASON_LEN = 10


def decision_validation_error(
    action: str | None, payload: dict[str, Any], finding: Finding
) -> str | None:
    """Return a rejection code, or None if valid."""
    if not action:
        return "invalid"
    reason = (payload.get("reason") or "").strip()
    needs_reason = action in ("reject", "escalate", "reopen", "override")
    if action == "edit":
        edits = payload.get("edits") or {}
        if "severity" in edits and edits["severity"] != finding.severity:
            needs_reason = True
    if needs_reason and len(reason) < MIN_REASON_LEN:
        return "invalid"
    if action == "escalate" and not payload.get("assigneeId"):
        return "invalid"
    return None
