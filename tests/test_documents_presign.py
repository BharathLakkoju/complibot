from unittest.mock import AsyncMock, MagicMock, patch

import boto3
import pytest
from botocore.config import Config
from botocore.exceptions import ClientError
from complibot.config import Settings
from complibot.exceptions import ServiceUnavailable
from complibot.main import app
from complibot.services import aws as aws_service
from httpx import ASGITransport, AsyncClient


def test_presign_put_params_match_real_s3_signer() -> None:
    """Presign params must be accepted by botocore's SigV4 presigner (offline)."""
    client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
        aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        config=Config(signature_version="s3v4"),
    )
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": "complibot-demo-documents-123456789012",
            "Key": "ten_proj_doc/sample.txt",
            "ContentType": "text/plain",
        },
        ExpiresIn=300,
    )
    assert "X-Amz-Algorithm=AWS4-HMAC-SHA256" in url
    assert "X-Amz-Signature=" in url


@pytest.mark.asyncio
async def test_ensure_bucket_uses_head_bucket_not_list_buckets() -> None:
    settings = Settings(s3_bucket="complibot-demo", aws_region="us-east-1")
    mock_s3 = AsyncMock()
    mock_s3.head_bucket = AsyncMock()
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("aioboto3.Session") as session_cls:
        session_cls.return_value.client.return_value = mock_cm
        await aws_service.ensure_bucket(settings)

    mock_s3.head_bucket.assert_awaited_once_with(Bucket="complibot-demo")
    mock_s3.list_buckets.assert_not_called()


@pytest.mark.asyncio
async def test_presign_put_maps_client_error_to_service_unavailable() -> None:
    settings = Settings(s3_bucket="b", aws_region="us-east-1")
    mock_s3 = AsyncMock()
    mock_s3.generate_presigned_url = AsyncMock(
        side_effect=ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "PutObject",
        )
    )
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("aioboto3.Session") as session_cls:
        session_cls.return_value.client.return_value = mock_cm
        with pytest.raises(ServiceUnavailable, match="upload URL"):
            await aws_service.presign_put(settings, "k", "text/plain")


async def _register(client: AsyncClient, email: str) -> dict[str, str]:
    res = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "securepass1"},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


@pytest.mark.asyncio
async def test_presign_endpoint_returns_problem_json_on_s3_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_presign(*_a, **_k):
        raise ServiceUnavailable("Could not prepare upload URL.")

    async def noop_bucket(*_a, **_k):
        return None

    monkeypatch.setattr("complibot.routers.documents.ensure_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.presign_put", fail_presign)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _register(client, "presign-fail@example.com")
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "P", "frameworkCodes": ["GDPR"]},
        )
        project_id = project.json()["id"]
        res = await client.post(
            f"/v1/projects/{project_id}/documents/presign",
            headers=headers,
            json={
                "filename": "note.txt",
                "contentType": "text/plain",
                "sizeBytes": 12,
            },
        )
        assert res.status_code == 503
        body = res.json()
        assert body["title"] == "unavailable"
        assert "upload URL" in body["detail"]


@pytest.mark.asyncio
async def test_presign_happy_path_with_mocked_s3(monkeypatch: pytest.MonkeyPatch) -> None:
    async def noop_bucket(*_a, **_k):
        return None

    async def fake_presign(_settings, key, content_type):
        assert content_type == "text/plain"
        assert key.endswith("/note.txt")
        return "https://s3.example/upload"

    monkeypatch.setattr("complibot.routers.documents.ensure_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.presign_put", fake_presign)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _register(client, "presign-ok@example.com")
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "P", "frameworkCodes": ["GDPR"]},
        )
        project_id = project.json()["id"]
        res = await client.post(
            f"/v1/projects/{project_id}/documents/presign",
            headers=headers,
            json={
                "filename": "note.txt",
                "contentType": "text/plain",
                "sizeBytes": 12,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["uploadUrl"] == "https://s3.example/upload"
        assert data["documentId"].startswith("doc_")
