import json
from urllib.parse import quote


class Url:
    def __init__(self, state: str, property_type: str, bed_min: int, bed_max: int, bath_min: int, bath_max: int):
        self.state = state
        self.property_type = property_type
        self.bed_min = bed_min
        self.bed_max = bed_max
        self.bath_min = bath_min
        self.bath_max = bath_max
        self.property_types = ["single-family-home", "townhome", "multi-family-home"]

    def the_property_type(self) -> str:
        if not self.property_type:
            raise ValueError("Property type must be provided.")
        if self.property_type not in self.property_types:
            raise ValueError(
                f"Invalid property type: {self.property_type}. Valid types are: {', '.join(self.property_types)}")
        return f"/type-{self.property_type}"

    def beds(self) -> str:
        if self.bed_min:
            if self.bed_max:
                return f"/beds-{self.bed_min}-{self.bed_max}"
            return f"/beds-{self.bed_min}"
        else:
            if self.bed_max:
                return f"/beds-na-{self.bed_max}"
            return "None"

    def baths(self) -> str:
        if self.bath_min:
            if self.bath_max:
                return f"/baths-{self.bath_min}-{self.bath_max}"
            return f"/baths-{self.bath_min}"
        else:
            if self.bath_max:
                return f"/baths-na-{self.bath_max}"
            return ""

    def __str__(self) -> str:
        if not self.state:
            raise ValueError("State must be provided to generate URL.")

        return f"https://www.realtor.com/realestateandhomes-search/{self.state}" + self.the_property_type() + self.beds() + self.baths()


TEST_URL = Url(state="Indiana", property_type="single-family-home", bed_min=10, bed_max=None, bath_min=None, bath_max=None)

# Example usage:
if __name__ == "__main__":
    print(TEST_URL)
