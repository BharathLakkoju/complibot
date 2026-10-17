mock_provider "aws" {
  mock_data "aws_caller_identity" {
    defaults = {
      account_id = "123456789012"
    }
  }
  mock_data "aws_iam_policy_document" {
    defaults = {
      json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}"
    }
  }
}

variables {
  ssh_cidr   = "203.0.113.10/32"
  api_domain = "203-0-113-50.sslip.io"
  acme_email = "ops@example.com"
}

run "dev_login_disabled_by_default" {
  command = apply

  assert {
    condition     = strcontains(aws_instance.app.user_data, "\nDEV_LOGIN_ENABLED=false\n")
    error_message = "default user_data must render DEV_LOGIN_ENABLED=false"
  }
  assert {
    condition     = strcontains(aws_instance.app.user_data, "\nCORS_ORIGINS=https://203-0-113-50.sslip.io\n")
    error_message = "CORS_ORIGINS must default to the single public origin"
  }
  assert {
    condition     = strcontains(aws_instance.app.user_data, "scripts/deploy-ec2.sh")
    error_message = "user_data must run scripts/deploy-ec2.sh on first boot"
  }
  assert {
    condition     = strcontains(aws_instance.app.user_data, "/var/log/complibot-deploy.log")
    error_message = "user_data must log deploy output to /var/log/complibot-deploy.log"
  }
  assert {
    condition     = contains(flatten([for r in aws_s3_bucket_cors_configuration.documents.cors_rule : r.allowed_origins]), "https://203-0-113-50.sslip.io")
    error_message = "S3 presigned PUT CORS must allow the single public origin"
  }
}

run "dev_login_enabled_for_public_demo" {
  command = apply

  variables {
    dev_login_enabled    = true
    cors_allowed_origins = ["https://203-0-113-50.sslip.io", "https://extra.example.com"]
  }

  assert {
    condition     = strcontains(aws_instance.app.user_data, "\nDEV_LOGIN_ENABLED=true\n")
    error_message = "dev_login_enabled = true must render DEV_LOGIN_ENABLED=true"
  }
  assert {
    condition     = strcontains(aws_instance.app.user_data, "\nCORS_ORIGINS=https://203-0-113-50.sslip.io,https://extra.example.com\n")
    error_message = "extra origins are appended once, without duplicating api_domain"
  }
}
