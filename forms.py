"""Validation for the search form and price guesses."""

import re

STATES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
}

MAX_ROOMS = 20
MAX_GUESS = 10_000_000_000

_GUESS_RE = re.compile(r"^(\d+(?:\.\d+)?)([km])?$")


def _number(raw, label, errors, key, integer):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        errors[key] = f"{label} must be a number."
        return None
    if value < 0 or value > MAX_ROOMS:
        errors[key] = f"{label} must be between 0 and {MAX_ROOMS}."
        return None
    if integer:
        if not value.is_integer():
            errors[key] = f"{label} must be a whole number."
            return None
        return int(value)
    if not (value * 2).is_integer():
        errors[key] = f"{label} must be a whole or half number, like 2 or 2.5."
        return None
    return int(value) if value.is_integer() else value


def validate_search(form):
    """Return (criteria, errors). `errors` maps field name to a message."""
    errors = {}
    state = (form.get("state") or "").strip().upper()
    if not state:
        errors["state"] = "Choose a state."
    elif state not in STATES:
        errors["state"] = "Choose a state from the list."

    bed_min = _number(form.get("bed_min"), "Min bedrooms", errors, "bed_min", integer=True)
    bed_max = _number(form.get("bed_max"), "Max bedrooms", errors, "bed_max", integer=True)
    bath_min = _number(form.get("bath_min"), "Min bathrooms", errors, "bath_min", integer=False)
    bath_max = _number(form.get("bath_max"), "Max bathrooms", errors, "bath_max", integer=False)

    if bed_min is not None and bed_max is not None and bed_min > bed_max:
        errors["bed_max"] = "Max bedrooms can't be less than min bedrooms."
    if bath_min is not None and bath_max is not None and bath_min > bath_max:
        errors["bath_max"] = "Max bathrooms can't be less than min bathrooms."

    criteria = {
        "state": state,
        "bed_min": bed_min,
        "bed_max": bed_max,
        "bath_min": bath_min,
        "bath_max": bath_max,
    }
    return criteria, errors


def parse_guess(text):
    """Turn "$450,000", "450000" or "450k" into whole dollars, or None if invalid."""
    cleaned = (text or "").strip().lower().replace("$", "").replace(",", "").replace(" ", "")
    match = _GUESS_RE.match(cleaned)
    if not match:
        return None
    value = float(match.group(1)) * {"k": 1_000, "m": 1_000_000}.get(match.group(2), 1)
    value = round(value)
    if value <= 0 or value > MAX_GUESS:
        return None
    return value
