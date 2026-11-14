"""The Listing record and price parsing."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_MONEY_RE = re.compile(r"\$\s*(\d[\d,]*(?:\.\d+)?)\s*([KMB])?\b", re.IGNORECASE)
_SUFFIX = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}


def parse_price(text):
    """Turn a listing price like "$1,250,000" or "$2.1M" into whole dollars.

    Returns None for anything that isn't a sale price: missing text,
    rentals ("$2,400/mo") and placeholder text.
    """
    if not text:
        return None
    lower = text.lower()
    if "/mo" in lower or "per month" in lower:
        return None
    match = _MONEY_RE.search(text)
    if not match:
        return None
    number = float(match.group(1).replace(",", ""))
    suffix = (match.group(2) or "").lower()
    value = round(number * _SUFFIX.get(suffix, 1))
    return value if value > 0 else None


@dataclass(frozen=True)
class Listing:
    url: str
    address: str
    price: int | None
    price_text: str
    beds: str = "N/A"
    baths: str = "N/A"
    sqft: str = "N/A"
    land_area: str = "N/A"
    year_built: str = "N/A"
    image_urls: tuple = field(default_factory=tuple)
