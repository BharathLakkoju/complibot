from urllib.parse import urlparse

import boto3
from complibot.config import Settings
from complibot.services.aws import s3_client_kwargs


def test_production_presigned_put_uses_regional_virtual_host() -> None:
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
    s3 = boto3.client("s3", **s3_client_kwargs(settings))
    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": "tenant/doc.txt", "ContentType": "text/plain"},
        ExpiresIn=300,
    )
    host = urlparse(url).netloc
    assert host == f"{bucket}.s3.{region}.amazonaws.com"
    assert host.endswith(".s3.amazonaws.com") is False


def test_localstack_presigned_put_keeps_custom_endpoint_host() -> None:
    settings = Settings(
        aws_endpoint_url="http://localhost:4566",
        aws_region="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        s3_bucket="complibot-demo",
    )
    s3 = boto3.client("s3", **s3_client_kwargs(settings))
    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.s3_bucket, "Key": "k", "ContentType": "text/plain"},
        ExpiresIn=300,
    )
    assert urlparse(url).netloc == "localhost:4566"
