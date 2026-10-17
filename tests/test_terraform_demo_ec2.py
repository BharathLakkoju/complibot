"""Terraform demo EC2 bootstrap wiring (no apply)."""

from pathlib import Path

_DEMO = Path("infra/terraform/envs/demo")


def test_dev_login_enabled_variable_and_user_data() -> None:
    variables = (_DEMO / "variables.tf").read_text()
    assert 'variable "dev_login_enabled"' in variables
    assert "default     = false" in variables

    ec2 = (_DEMO / "ec2.tf").read_text()
    assert "dev_login_enabled   = var.dev_login_enabled" in ec2

    user_data = (_DEMO / "user_data.sh.tpl").read_text()
    assert "DEV_LOGIN_ENABLED=${dev_login_enabled}" in user_data
