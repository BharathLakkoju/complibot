"""Create S3 bucket and SQS queue in LocalStack."""

import boto3

from complibot.config import get_settings


def main() -> None:
    settings = get_settings()
    endpoint = settings.aws_endpoint_url or "http://localhost:4566"
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
    sqs = boto3.client(
        "sqs",
        endpoint_url=endpoint,
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
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
