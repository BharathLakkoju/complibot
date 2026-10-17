"""Render the demo EC2 user-data template with Terraform's own templatefile()."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

_TEMPLATE = Path("infra/terraform/envs/demo/user_data.sh.tpl").resolve()

pytestmark = pytest.mark.skipif(
    shutil.which("terraform") is None, reason="terraform CLI not installed"
)


def _render(tmp_path: Path, dev_login_enabled: bool) -> str:
    template_vars = {
        "repository_url": "https://github.com/example/complibot.git",
        "aws_region": "ap-south-1",
        "s3_bucket": "docs-bucket",
        "backup_bucket": "backup-bucket",
        "sqs_queue_url": "https://sqs.example/queue",
        "api_domain": "203-0-113-50.sslip.io",
        "acme_email": "ops@example.com",
        "cors_origins": "https://203-0-113-50.sslip.io",
    }
    hcl_vars = ", ".join(f"{k} = {json.dumps(v)}" for k, v in template_vars.items())
    expr = (
        f"jsonencode(templatefile({json.dumps(str(_TEMPLATE))}, "
        f"{{ {hcl_vars}, dev_login_enabled = {str(dev_login_enabled).lower()} }}))"
    )
    out = subprocess.run(
        ["terraform", "console"],
        input=expr,
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=True,
        timeout=60,
    ).stdout
    # console prints the jsonencode() result as an HCL string literal: decode twice.
    return json.loads(json.loads(out.strip()))


@pytest.mark.parametrize("enabled", [True, False])
def test_dev_login_enabled_renders_into_env_bootstrap(tmp_path: Path, enabled: bool) -> None:
    lines = _render(tmp_path, enabled).splitlines()
    assert [ln for ln in lines if ln.startswith("DEV_LOGIN_ENABLED=")] == [
        f"DEV_LOGIN_ENABLED={str(enabled).lower()}"
    ]
    assert "API_DOMAIN=203-0-113-50.sslip.io" in lines
    assert "CORS_ORIGINS=https://203-0-113-50.sslip.io" in lines


def test_user_data_invokes_deploy_ec2(tmp_path: Path) -> None:
    rendered = _render(tmp_path, dev_login_enabled=False)
    assert "scripts/deploy-ec2.sh" in rendered
    assert "/var/log/complibot-deploy.log" in rendered
    assert "runuser -u ec2-user" in rendered
    assert "install -m 0600" in rendered
    assert "/opt/complibot/.env.bootstrap" in rendered
