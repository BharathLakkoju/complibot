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
        "llm_provider": "mock",
        "openrouter_model": "nvidia/nemotron-3-ultra-550b-a55b:free",
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
    assert "LLM_PROVIDER=mock" in lines
    assert "OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free" in lines


_DEPLOY_TAIL_START = "if [ ! -f /opt/complibot/.env ]; then"

_STUBS = {
    "runuser": 'echo "runuser $*"\nexit "${STUB_DEPLOY_RC:-0}"\n',
    # install -m MODE -o USER -g GROUP SRC DST
    "install": 'cp "${@: -2:1}" "${@: -1}"\n',
    "chown": "exit 0\n",
}


def _run_deploy_tail(
    tmp_path: Path, deploy_rc: int, existing_env: str | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the rendered user-data tail (after bootstrap/chown) with root-only tools stubbed."""
    rendered = _render(tmp_path, dev_login_enabled=False)
    assert _DEPLOY_TAIL_START in rendered, "user_data no longer creates .env before deploy"
    repo = tmp_path / "opt"
    repo.mkdir()
    (repo / ".env.bootstrap").write_text("FROM=bootstrap\n")
    if existing_env is not None:
        (repo / ".env").write_text(existing_env)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in _STUBS.items():
        stub = bin_dir / name
        stub.write_text(f"#!/bin/bash\n{body}")
        stub.chmod(0o755)
    tail = rendered[rendered.index(_DEPLOY_TAIL_START) :]
    tail = tail.replace("/var/log/complibot-deploy.log", str(tmp_path / "deploy.log"))
    tail = tail.replace("/opt/complibot", str(repo))
    return subprocess.run(
        ["bash", "-c", "set -euo pipefail\n" + tail],
        capture_output=True,
        text=True,
        env={"PATH": f"{bin_dir}:/usr/bin:/bin", "STUB_DEPLOY_RC": str(deploy_rc)},
        timeout=30,
    )


def test_user_data_runs_deploy_as_ec2_user(tmp_path: Path) -> None:
    result = _run_deploy_tail(tmp_path, deploy_rc=0)
    assert result.returncode == 0, result.stderr
    log = (tmp_path / "deploy.log").read_text()
    deploy_cmd = f"cd {tmp_path}/opt && exec ./scripts/deploy-ec2.sh"
    assert f"runuser -u ec2-user -- bash -lc {deploy_cmd}" in log
    assert (tmp_path / "opt" / ".env").read_text() == "FROM=bootstrap\n"


def test_user_data_keeps_existing_env(tmp_path: Path) -> None:
    result = _run_deploy_tail(tmp_path, deploy_rc=0, existing_env="EDITED=1\n")
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "opt" / ".env").read_text() == "EDITED=1\n"


def test_user_data_tolerates_https_not_ready(tmp_path: Path) -> None:
    result = _run_deploy_tail(tmp_path, deploy_rc=75)
    assert result.returncode == 0, result.stderr
    assert "HTTPS not ready yet" in result.stderr


@pytest.mark.parametrize("deploy_rc", [1, 2, 128])
def test_user_data_fails_cloud_init_on_deploy_error(tmp_path: Path, deploy_rc: int) -> None:
    result = _run_deploy_tail(tmp_path, deploy_rc=deploy_rc)
    assert result.returncode == deploy_rc
    assert f"complibot deploy failed (exit {deploy_rc})" in result.stderr
