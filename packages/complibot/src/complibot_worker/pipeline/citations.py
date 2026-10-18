"""Citation offset verification for review findings."""

from __future__ import annotations

from complibot.schemas import FindingKind, Severity

_SEVERITIES: set[str] = {"critical", "high", "medium", "low", "info"}
_KINDS: set[str] = {"violation", "gap", "partial", "compliant"}


def coerce_severity(value: object) -> Severity:
    s = str(value or "medium").lower()
    return s if s in _SEVERITIES else "medium"


def coerce_kind(value: object) -> FindingKind | None:
    s = str(value or "").lower()
    return s if s in _KINDS else None


def locate_verified_citation(text: str, quote: str) -> tuple[int, int, str] | None:
    """Return char offsets only when quote is an exact verbatim slice of text."""
    if not quote:
        return None
    idx = text.find(quote)
    if idx < 0:
        return None
    end = idx + len(quote)
    slice_ = text[idx:end]
    if slice_ != quote:
        return None
    return idx, end, slice_
