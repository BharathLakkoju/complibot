from datetime import UTC, datetime

import pytest
from complibot.schemas import Confidence, Finding, FindingProvenance
from complibot.ws.decisions import decision_validation_error


def _finding() -> Finding:
    now = datetime.now(UTC)
    return Finding(
        id="fnd_test",
        tenant_id="ten_test",
        project_id="prj_test",
        review_id="rev_test",
        framework="GDPR",
        control_id="c1",
        control_ref="GDPR-1",
        kind="gap",
        title="t",
        severity="medium",
        confidence=Confidence(score=0.5, band="medium", reason="r", calibrated=False),
        rationale="r",
        citations=[],
        provenance=FindingProvenance(model_id="m", prompt_version="p", pack_version="v"),
        created_at=now,
    )


def test_reject_requires_reason() -> None:
    f = _finding()
    assert decision_validation_error("reject", {"reason": "short"}, f) == "invalid"
    assert decision_validation_error("reject", {"reason": "long enough reason"}, f) is None


def test_escalate_requires_assignee() -> None:
    f = _finding()
    assert (
        decision_validation_error(
            "escalate",
            {"reason": "long enough reason"},
            f,
        )
        == "invalid"
    )


@pytest.mark.parametrize("action", [None, "", "comment", "delete", "ACCEPT"])
def test_unknown_actions_rejected(action: str | None) -> None:
    assert decision_validation_error(action, {"reason": "long enough reason"}, _finding()) == (
        "invalid"
    )


def test_override_requires_valid_override_action_and_reason() -> None:
    f = _finding()
    reason = {"reason": "owner override reason"}
    assert decision_validation_error("override", reason, f) == "invalid"
    assert decision_validation_error("override", {**reason, "overrideAction": "reopen"}, f) == (
        "invalid"
    )
    assert decision_validation_error("override", {"overrideAction": "accept"}, f) == "invalid"
    assert decision_validation_error("override", {**reason, "overrideAction": "accept"}, f) is None


def test_edit_validation() -> None:
    f = _finding()
    assert decision_validation_error("edit", {}, f) == "invalid"
    assert decision_validation_error("edit", {"edits": {"status": "accepted"}}, f) == "invalid"
    assert decision_validation_error("edit", {"edits": {"title": "new"}}, f) is None
    assert decision_validation_error("edit", {"edits": {"severity": "high"}}, f) == "invalid"
    assert (
        decision_validation_error(
            "edit", {"edits": {"severity": "high"}, "reason": "risk is higher"}, f
        )
        is None
    )
