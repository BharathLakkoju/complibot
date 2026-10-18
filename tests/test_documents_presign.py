from urllib.parse import urlparse

import pytest
from complibot.config import Settings
from complibot.services.aws import presign_put


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
    url = await presign_put(settings, "tenant/doc.txt", "text/plain")
    host = urlparse(url).netloc
    assert host == f"{bucket}.s3.{region}.amazonaws.com"
    assert host.endswith(".s3.amazonaws.com") is False
    assert "." not in bucket  # demo bucket: no dots, so virtual-hosted TLS is safe


@pytest.mark.asyncio
async def test_localstack_presigned_put_keeps_custom_endpoint_host() -> None:
    settings = Settings(
        aws_endpoint_url="http://localhost:4566",
        aws_region="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        s3_bucket="complibot-demo",
    )
    url = await presign_put(settings, "k", "text/plain")
    assert urlparse(url).netloc == "localhost:4566"
