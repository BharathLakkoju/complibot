import pytest
from complibot.config import Settings
from complibot.exceptions import BadRequest
from complibot.services.queue import dispatch_review_job


@pytest.mark.asyncio
async def test_sqs_failure_does_not_inline_when_worker_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        app_env="local",
        dev_login_enabled=True,
        inline_worker=False,
        aws_endpoint_url="http://localhost:9",
        sqs_queue_url="http://localhost:9/000000000000/q",
    )

    async def fail_enqueue(_settings: Settings, _body: dict) -> None:
        raise OSError("connection refused")

    monkeypatch.setattr("complibot.services.queue.enqueue_review_job", fail_enqueue)

    with pytest.raises(BadRequest):
        await dispatch_review_job(settings, {"reviewId": "rev_x", "tenantId": "ten_x"})
