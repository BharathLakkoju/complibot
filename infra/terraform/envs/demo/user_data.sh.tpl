#!/bin/bash
set -euo pipefail

dnf update -y
dnf install -y docker docker-compose-plugin git awscli
systemctl enable --now docker
usermod -aG docker ec2-user

mkdir -p /opt/complibot
if [ ! -d /opt/complibot/.git ]; then
  git clone "${repository_url}" /opt/complibot
fi

cat >/opt/complibot/.env.bootstrap <<EOF
APP_ENV=demo
AWS_REGION=${aws_region}
S3_BUCKET=${s3_bucket}
BACKUP_S3_BUCKET=${backup_bucket}
SQS_QUEUE_URL=${sqs_queue_url}
AWS_ENDPOINT_URL=
INLINE_WORKER=false
LLM_PROVIDER=mock
DEV_LOGIN_ENABLED=false
API_DOMAIN=${api_domain}
ACME_EMAIL=${acme_email}
CORS_ORIGINS=${cors_origins}
EOF

chown -R ec2-user:ec2-user /opt/complibot
