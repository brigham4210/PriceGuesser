import json
from urllib.parse import quote


class Url:
    def __init__(self, state: str, bed_min: int, bed_max: int, bath_min: int, bath_max: int):
        self.state = state
        self.bed_min = bed_min
        self.bed_max = bed_max
        self.bath_min = bath_min
        self.bath_max = bath_max

    def json(self):
        data = {
            "filterState": {
                "beds": {"min": self.bed_min, "max": self.bed_max},
                "baths": {"min": self.bath_min, "max": self.bath_max}
            }
        }
        return json.dumps(data)

    def __str__(self) -> str:
        if not self.state:
            raise ValueError("State must be provided to generate URL.")

        return f"https://www.zillow.com/{self.state.lower()}/?searchQueryState={quote(self.json())}"


# Example usage:
if __name__ == "__main__":
    test_url = Url(state="in", bed_min=10, bed_max=None, bath_min=None, bath_max=None)
    print(test_url.json())
    print(test_url)
