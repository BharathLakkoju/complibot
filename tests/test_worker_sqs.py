import json
from typing import Any

import pytest
from complibot_worker import main as worker


class FakeSqs:
    def __init__(self) -> None:
        self.deleted: list[str] = []

    async def delete_message(self, QueueUrl: str, ReceiptHandle: str) -> None:  # noqa: N803
        self.deleted.append(ReceiptHandle)

    async def change_message_visibility(self, **_kw: Any) -> None:
        return None


def _msg(receives: int = 1) -> dict[str, Any]:
    return {
        "ReceiptHandle": "rh-1",
        "Body": json.dumps({"reviewId": "rev_x", "tenantId": "ten_x"}),
        "Attributes": {"ApproximateReceiveCount": str(receives)},
    }


async def test_message_deleted_only_after_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []

    async def ok(_body: dict, *, final_attempt: bool = False) -> None:
        calls.append(final_attempt)

    monkeypatch.setattr(worker, "process_message", ok)
    sqs = FakeSqs()
    await worker._handle_sqs_message(sqs, "q", _msg())
    assert sqs.deleted == ["rh-1"]
    assert calls == [False]


@pytest.mark.parametrize("receives,final", [(1, False), (worker.MAX_RECEIVES, True)])
async def test_failed_message_left_for_retry_or_dlq(
    monkeypatch: pytest.MonkeyPatch, receives: int, final: bool
) -> None:
    seen: list[bool] = []

    async def boom(_body: dict, *, final_attempt: bool = False) -> None:
        seen.append(final_attempt)
        raise RuntimeError("pipeline failed")

    monkeypatch.setattr(worker, "process_message", boom)
    sqs = FakeSqs()
    await worker._handle_sqs_message(sqs, "q", _msg(receives))
    assert sqs.deleted == []
    assert seen == [final]


async def test_malformed_body_is_not_deleted() -> None:
    sqs = FakeSqs()
    await worker._handle_sqs_message(sqs, "q", {"ReceiptHandle": "rh-2", "Body": "{"})
    assert sqs.deleted == []
