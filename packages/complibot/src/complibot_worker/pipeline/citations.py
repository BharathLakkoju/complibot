"""Citation offset verification for review findings."""

from __future__ import annotations

import re

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
    """Return char offsets when quote matches a contiguous excerpt of text (original casing)."""
    if not quote:
        return None
    idx = text.find(quote)
    if idx >= 0:
        end = idx + len(quote)
        slice_ = text[idx:end]
        if slice_ == quote:
            return idx, end, slice_

    lower_text = text.lower()
    lower_quote = quote.lower()
    idx = lower_text.find(lower_quote)
    if idx >= 0:
        end = idx + len(quote)
        return idx, end, text[idx:end]

    words = [w for w in quote.split() if w]
    if not words:
        return None
    pattern = r"\s+".join(re.escape(word) for word in words)
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        return None
    start, end = match.start(), match.end()
    return start, end, text[start:end]
