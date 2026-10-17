from datetime import UTC, datetime

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
