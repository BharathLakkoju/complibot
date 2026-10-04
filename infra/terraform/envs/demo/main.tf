# Demo environment skeleton — extend per ai/build/skills/deploy-to-aws/SKILL.md
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

output "status" {
  value = "Terraform modules not yet applied — local docker-compose stack is the default dev path."
}
