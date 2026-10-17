provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      project     = var.project
      environment = var.environment
      managed_by  = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_ami" "al2023_arm" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-kernel-*-arm64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

locals {
  name_prefix        = "${var.project}-${var.environment}"
  bucket_name        = "${var.project}-${var.environment}-documents-${data.aws_caller_identity.current.account_id}"
  backup_bucket_name = "${var.project}-${var.environment}-backups-${data.aws_caller_identity.current.account_id}"
}
