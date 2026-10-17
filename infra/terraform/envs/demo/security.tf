resource "aws_security_group" "app" {
  name        = "${local.name_prefix}-ec2"
  description = "CompliBot single-EC2 demo"

  ingress {
    description = "SSH (restrict ssh_cidr before production use)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  ingress {
    description = "HTTP for Let's Encrypt HTTP-01 and Caddy redirect to HTTPS"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.api_cidr]
  }

  ingress {
    description = "HTTPS (Caddy → API on localhost)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.api_cidr]
  }

  egress {
    description = "Outbound for dnf, image pulls, ACME, S3 and SQS endpoints"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
