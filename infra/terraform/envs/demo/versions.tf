terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment after bootstrap (see docs/deploy/aws/04-terraform-state-bootstrap.md):
  # backend "s3" {
  #   bucket       = "complibot-tfstate-demo-ap-south-1"
  #   key          = "ec2-demo/terraform.tfstate"
  #   region       = "ap-south-1"
  #   encrypt      = true
  #   use_lockfile = true
  # }
}
