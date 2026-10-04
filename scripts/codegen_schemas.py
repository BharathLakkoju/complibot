"""Copy machine-readable schemas from ai/ into packages/schemas (codegen stub)."""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "ai" / "agents" / "schemas"
DST = ROOT / "packages" / "schemas"


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    for name in ("finding.schema.yaml", "events.yaml"):
        shutil.copy2(SRC / name, DST / name)
    print(f"Synced schemas to {DST}")


if __name__ == "__main__":
    main()
