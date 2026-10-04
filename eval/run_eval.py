#!/usr/bin/env python3
"""Eval harness CLI skeleton (gold v0 smoke)."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="eval run")
    parser.add_argument("--gold", default="v0")
    parser.add_argument("--frameworks", default="GDPR,SOC2")
    parser.add_argument("--prompt-version", default="mock-1")
    args = parser.parse_args()
    out = {
        "gold": args.gold,
        "frameworks": args.frameworks.split(","),
        "promptVersion": args.prompt_version,
        "generatedAt": datetime.now(UTC).isoformat(),
        "metrics": {
            "status": "not_yet_measured",
            "citationExistence": None,
            "f1": None,
        },
    }
    results_dir = Path("eval/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / "local-smoke.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
