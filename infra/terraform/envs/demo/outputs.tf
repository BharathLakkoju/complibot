output "public_ip" {
  description = "Elastic IP for SSH and API access."
  value       = aws_eip.app.public_ip
}

output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.app.id
}

output "s3_bucket" {
  description = "Application documents bucket."
  value       = aws_s3_bucket.documents.bucket
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
