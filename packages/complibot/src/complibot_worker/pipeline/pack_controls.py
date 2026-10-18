"""Load confirmed controls from framework pack YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_FRAMEWORK_FOLDER = {
    "GDPR": "gdpr",
    "SOC2": "soc2",
    "ISO27001": "iso27001",
    "HIPAA": "hipaa",
    "INTERNAL": "internal-policy",
}


def load_pack_controls(framework: str, frameworks_path: str) -> list[dict[str, Any]]:
    folder = _FRAMEWORK_FOLDER.get(framework)
    if not folder:
        return []
    pack_path = Path(frameworks_path) / folder / "pack.yaml"
    if not pack_path.exists():
        return []
    data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    controls = data.get("controls", [])
    return [c for c in controls if c.get("verify") == "confirmed"]


def control_ref(ctrl: dict[str, Any]) -> str:
    return str(ctrl.get("ref") or ctrl.get("id", ""))
