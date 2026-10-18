from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlparse

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
    """Same Params helper as production presign_put — offline SigV4 validation."""
    params = aws_service.presign_put_object_params(
        "complibot-demo-documents-123456789012",
        "ten_proj_doc/sample.txt",
        "text/plain",
    )
    client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
        aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        config=Config(signature_version="s3v4"),
    )
    url = client.generate_presigned_url(
        "put_object",
        Params=params,
        ExpiresIn=300,
    )
    assert "X-Amz-Algorithm=AWS4-HMAC-SHA256" in url
    assert "X-Amz-Signature=" in url


@pytest.mark.asyncio
async def test_maybe_ensure_skipped_without_local_endpoint() -> None:
    settings = Settings(
        s3_bucket="complibot-demo",
        aws_region="us-east-1",
        aws_endpoint_url=None,
    )
    with patch("complibot.services.aws.ensure_bucket", new_callable=AsyncMock) as ensure:
        await aws_service.maybe_ensure_documents_bucket(settings)
        ensure.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_bucket_uses_head_bucket_not_list_buckets() -> None:
    settings = Settings(
        s3_bucket="complibot-demo",
        aws_region="us-east-1",
        aws_endpoint_url="http://localhost:4566",
    )
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
async def test_ensure_bucket_head_access_denied_raises_service_unavailable() -> None:
    """IAM denial on HeadBucket (s3:ListBucket) must not surface as HTTP 500."""
    settings = Settings(
        s3_bucket="complibot-demo",
        aws_region="us-east-1",
        aws_endpoint_url="http://localhost:4566",
    )
    mock_s3 = AsyncMock()
    mock_s3.head_bucket = AsyncMock(
        side_effect=ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "not authorized"}},
            "HeadBucket",
        )
    )
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("aioboto3.Session") as session_cls:
        session_cls.return_value.client.return_value = mock_cm
        with pytest.raises(ServiceUnavailable, match="unavailable"):
            await aws_service.ensure_bucket(settings)

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
async def test_presign_bad_mime_returns_400_not_503(monkeypatch: pytest.MonkeyPatch) -> None:
    async def boom(*_a, **_k):
        raise AssertionError("S3 must not be called for invalid mime")

    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", boom)
    monkeypatch.setattr("complibot.routers.documents.presign_put", boom)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _register(client, "bad-mime@example.com")
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
                "filename": "evil.exe",
                "contentType": "application/octet-stream",
                "sizeBytes": 12,
            },
        )
        assert res.status_code == 400
        assert res.json()["title"] == "bad_request"


@pytest.mark.asyncio
async def test_presign_endpoint_head_bucket_access_denied_returns_503_not_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: unhandled S3 AccessDenied (formerly list_buckets) must be 503 problem+json."""

    async def deny_bucket(_settings):
        raise ServiceUnavailable("Document storage is unavailable.")

    async def fake_presign(_settings, key, content_type):
        return "https://s3.example/upload"

    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", deny_bucket)
    monkeypatch.setattr("complibot.routers.documents.presign_put", fake_presign)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _register(client, "bucket-deny@example.com")
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
        assert res.status_code != 500
        body = res.json()
        assert body["title"] == "unavailable"


@pytest.mark.asyncio
async def test_presign_endpoint_returns_problem_json_on_s3_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_presign(*_a, **_k):
        raise ServiceUnavailable("Could not prepare upload URL.")

    async def noop_bucket(*_a, **_k):
        return None

    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)
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


def _production_like_settings() -> Settings:
    return Settings(
        s3_bucket="complibot-demo",
        aws_region="us-east-1",
        aws_endpoint_url=None,
    )


@pytest.mark.asyncio
async def test_presign_happy_path_with_mocked_s3(monkeypatch: pytest.MonkeyPatch) -> None:
    ensure_called = False

    async def track_ensure_bucket(*_a, **_k):
        nonlocal ensure_called
        ensure_called = True

    async def fake_presign(_settings, key, content_type):
        assert content_type == "text/plain"
        assert key.endswith("/note.txt")
        return "https://s3.example/upload"

    monkeypatch.setattr("complibot.routers.documents.get_settings", _production_like_settings)
    monkeypatch.setattr("complibot.services.aws.ensure_bucket", track_ensure_bucket)
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
        assert ensure_called is False


@pytest.mark.asyncio
async def test_app_error_handler_never_returns_500_for_service_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail(*_a, **_k):
        raise ServiceUnavailable("storage down")

    async def noop_bucket(*_a, **_k):
        return None

    monkeypatch.setattr("complibot.routers.documents.get_settings", _production_like_settings)
    monkeypatch.setattr("complibot.routers.documents.maybe_ensure_documents_bucket", noop_bucket)
    monkeypatch.setattr("complibot.routers.documents.presign_put", fail)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _register(client, "handler@example.com")
        project = await client.post(
            "/v1/projects",
            headers=headers,
            json={"name": "P", "frameworkCodes": ["GDPR"]},
        )
        res = await client.post(
            f"/v1/projects/{project.json()['id']}/documents/presign",
            headers=headers,
            json={
                "filename": "a.txt",
                "contentType": "text/plain",
                "sizeBytes": 4,
            },
        )
        assert res.status_code == 503
        assert "type" in res.json()


@pytest.mark.asyncio
async def test_production_presigned_put_uses_regional_virtual_host() -> None:
    """Presigned PUT must target the bucket's regional virtual-hosted endpoint."""
    bucket = "complibot-demo-documents-753227947131"
    region = "ap-south-1"
    settings = Settings(
        app_env="local",
        aws_endpoint_url=None,
        aws_region=region,
        aws_access_key_id="AKIATEST",
        aws_secret_access_key="secret",
        s3_bucket=bucket,
    )
    url = await aws_service.presign_put(settings, "tenant/doc.txt", "text/plain")
    host = urlparse(url).netloc
    assert host == f"{bucket}.s3.{region}.amazonaws.com"
    assert host.endswith(".s3.amazonaws.com") is False
    assert "." not in bucket


@pytest.mark.asyncio
async def test_localstack_presigned_put_keeps_custom_endpoint_host() -> None:
    settings = Settings(
        aws_endpoint_url="http://localhost:4566",
        aws_region="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        s3_bucket="complibot-demo",
    )
    url = await aws_service.presign_put(settings, "k", "text/plain")
    assert urlparse(url).netloc == "localhost:4566"
