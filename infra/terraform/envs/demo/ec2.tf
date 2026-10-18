resource "aws_instance" "app" {
  ami                    = data.aws_ami.al2023_arm.id
  instance_type          = var.instance_type
  iam_instance_profile   = aws_iam_instance_profile.ec2.name
  vpc_security_group_ids = [aws_security_group.app.id]
  key_name               = var.ssh_key_name != "" ? var.ssh_key_name : null
  ebs_optimized          = true

  # Hop limit 1 is enough: compose uses host networking, so containers reach IMDS directly.
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  monitoring = false

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_gb
    encrypted             = true
    delete_on_termination = true
  }

  user_data = templatefile("${path.module}/user_data.sh.tpl", {
    repository_url        = var.repository_url
    aws_region            = var.aws_region
    s3_bucket             = aws_s3_bucket.documents.bucket
    backup_bucket         = aws_s3_bucket.backups.bucket
    sqs_queue_url         = aws_sqs_queue.review.url
    api_domain            = var.api_domain
    acme_email            = var.acme_email
    cors_origins          = join(",", local.browser_origins)
    dev_login_enabled     = var.dev_login_enabled
    llm_provider          = var.llm_provider
    openrouter_model      = var.openrouter_model
    openrouter_secret_arn = aws_secretsmanager_secret.openrouter_api_key.arn
  })

  tags = {
    Name = "${local.name_prefix}-app"
  }
}

resource "aws_eip" "app" {
  domain = "vpc"

  tags = {
    Name = "${local.name_prefix}-eip"
  }
}

resource "aws_eip_association" "app" {
  instance_id   = aws_instance.app.id
  allocation_id = aws_eip.app.id
}
