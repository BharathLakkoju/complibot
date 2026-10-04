"""Validate framework pack.yaml control counts."""

from pathlib import Path

import yaml

EXPECTED = {
    "gdpr": 20,
    "soc2": 19,
    "iso27001": 22,
    "hipaa": 20,
    "internal-policy": 5,
}


def main() -> None:
    root = Path("ai/frameworks")
    errors: list[str] = []
    for folder, count in EXPECTED.items():
        pack = root / folder / "pack.yaml"
        if not pack.exists():
            errors.append(f"Missing {pack}")
            continue
        data = yaml.safe_load(pack.read_text(encoding="utf-8"))
        controls = data.get("controls", [])
        if len(controls) != count:
            errors.append(f"{folder}: expected {count} controls, got {len(controls)}")
    if errors:
        raise SystemExit("\n".join(errors))
    print("All packs validated.")


if __name__ == "__main__":
    main()
