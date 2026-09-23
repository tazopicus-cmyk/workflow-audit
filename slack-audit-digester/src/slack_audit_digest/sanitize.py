"""Strip em dashes from client-facing copy (locked F2 constraint)."""

from __future__ import annotations

import re

_DASHES = re.compile(r"[\u2014\u2013\u2212]")


def sanitize_copy(text: str) -> str:
    """Replace em/en/minus dashes with ASCII punctuation. Keep hyphens."""
    if not text:
        return text
    # Spaced em/en dash becomes ". ". Bare dash becomes ". ".
    text = re.sub(r"\s+[\u2014\u2013\u2212]\s+", ". ", text)
    text = _DASHES.sub(". ", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r" \.", ".", text)
    return text.strip()


def assert_no_em_dashes(text: str, label: str = "text") -> None:
    if not text:
        return
    for ch in ("\u2014", "\u2013"):
        if ch in text:
            raise ValueError(f"em/en dash found in {label}")
