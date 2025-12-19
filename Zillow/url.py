import json
from urllib.parse import quote


class Url:
    def __init__(self, state: str, bed_min: int, bed_max: int, bath_min: int, bath_max: int):
        self.state = state.lower().replace(',', '').replace(" ", "-")
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
                "land": {"value": False}
            }
        }
        return json.dumps(data)

    def __str__(self) -> str:
        if not self.state:
            raise ValueError("State must be provided to generate URL.")

        return f"https://www.zillow.com/{self.state}/?searchQueryState={quote(self.json())}"
