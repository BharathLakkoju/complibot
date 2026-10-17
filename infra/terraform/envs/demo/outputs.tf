output "public_ip" {
  description = "Elastic IP — point API_DOMAIN DNS A record here."
  value       = aws_eip.app.public_ip
}

output "api_base_url" {
  description = "HTTPS API base URL for Vercel NEXT_PUBLIC_API_URL (set API_DOMAIN on the host)."
  value       = "https://${var.api_domain}"
}

output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.app.id
}

output "s3_bucket" {
  description = "Application documents bucket."
  value       = aws_s3_bucket.documents.bucket
}

output "backup_s3_bucket" {
  description = "Postgres backup bucket (separate from application documents)."
  value       = aws_s3_bucket.backups.bucket
}

output "sqs_queue_url" {
  description = "Review job queue URL."
  value       = aws_sqs_queue.review.url
}

output "sqs_queue_arn" {
  description = "Review job queue ARN."
  value       = aws_sqs_queue.review.arn
}

output "security_group_id" {
  description = "EC2 security group ID."
  value       = aws_security_group.app.id
}
