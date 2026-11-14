"""Build Zillow search URLs."""

import json
from urllib.parse import quote


class Url:
    def __init__(self, state, bed_min=None, bed_max=None, bath_min=None, bath_max=None):
        if not state or not state.strip():
            raise ValueError("State must be provided to generate URL.")
        self.location = state.strip().lower().replace(",", "").replace(" ", "-")
        self.bed_min = bed_min
        self.bed_max = bed_max
        self.bath_min = bath_min
        self.bath_max = bath_max

    def json(self):
        data = {
            "filterState": {
                "beds": {"min": self.bed_min, "max": self.bed_max},
                "baths": {"min": self.bath_min, "max": self.bath_max},
                "mf": {"value": False},
                "con": {"value": False},
                "apa": {"value": False},
                "apco": {"value": False},
                "land": {"value": False},
            }
        }
        return json.dumps(data)

    def __str__(self):
        return f"https://www.zillow.com/{self.location}/?searchQueryState={quote(self.json())}"
