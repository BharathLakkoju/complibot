"""Create S3 bucket and SQS queue in LocalStack."""

import boto3
from complibot.config import get_settings
from complibot.services.aws import _client_kwargs, s3_client_kwargs


def main() -> None:
    settings = get_settings()
    if not settings.aws_endpoint_url:
        settings = settings.model_copy(update={"aws_endpoint_url": "http://localhost:4566"})
    s3 = boto3.client("s3", **s3_client_kwargs(settings))
    sqs = boto3.client("sqs", **_client_kwargs(settings))
    buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    if settings.s3_bucket not in buckets:
        s3.create_bucket(Bucket=settings.s3_bucket)
        print(f"Created bucket {settings.s3_bucket}")
    try:
        sqs.create_queue(QueueName="complibot-review")
        print("Created queue complibot-review")
    except Exception:
        pass


if __name__ == "__main__":
    main()
