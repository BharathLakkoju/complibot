resource "aws_sqs_queue" "review_dlq" {
  name                      = "${local.name_prefix}-review-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue" "review" {
  name                       = "${local.name_prefix}-review"
  visibility_timeout_seconds = 120
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.review_dlq.arn
    maxReceiveCount     = 3
  })
}
