import json
from urllib.parse import parse_qs, urlparse

import pytest

from forms import parse_guess, validate_search
from game import MAX_POINTS, score_guess
from Zillow.listing import parse_price
from Zillow.url import Url


class TestUrl:
    def test_builds_state_search_with_filters(self):
        url = urlparse(str(Url("CA", bed_min=2, bed_max=4, bath_min=1.5, bath_max=None)))
        assert url.netloc == "www.zillow.com"
        assert url.path == "/ca/"
        state = json.loads(parse_qs(url.query)["searchQueryState"][0])["filterState"]
        assert state["beds"] == {"min": 2, "max": 4}
        assert state["baths"] == {"min": 1.5, "max": None}
        assert state["land"] == {"value": False}

    @pytest.mark.parametrize("state", ["", "   ", None])
    def test_requires_state(self, state):
        with pytest.raises(ValueError):
            Url(state)


class TestParsePrice:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("$1,250,000", 1_250_000),
            ("$450000", 450_000),
            ("$2.1M", 2_100_000),
            ("$850K", 850_000),
            ("Est. $612,300", 612_300),
            ("$2,400/mo", None),
            ("Price not available", None),
            ("", None),
            (None, None),
            ("$0", None),
        ],
    )
    def test_cases(self, text, expected):
        assert parse_price(text) == expected


class TestParseGuess:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("$500,000", 500_000),
            ("500000", 500_000),
            (" 450k ", 450_000),
            ("1.2m", 1_200_000),
            ("$1.5M", 1_500_000),
        ],
    )
    def test_valid(self, text, expected):
        assert parse_guess(text) == expected

    @pytest.mark.parametrize("text", ["", None, "abc", "$", "-5", "0", "12.3.4", "5e5", "99999999999"])
    def test_invalid(self, text):
        assert parse_guess(text) is None


class TestValidateSearch:
    def test_valid_with_ranges(self):
        criteria, errors = validate_search(
            {"state": "ca", "bed_min": "2", "bed_max": "3", "bath_min": "1.5", "bath_max": ""}
        )
        assert errors == {}
        assert criteria == {"state": "CA", "bed_min": 2, "bed_max": 3, "bath_min": 1.5, "bath_max": None}

    def test_state_required_and_known(self):
        assert "state" in validate_search({"state": ""})[1]
        assert "state" in validate_search({"state": "XX"})[1]

    def test_min_greater_than_max(self):
        _, errors = validate_search({"state": "TX", "bed_min": "4", "bed_max": "2", "bath_min": "3", "bath_max": "1"})
        assert set(errors) == {"bed_max", "bath_max"}

    @pytest.mark.parametrize(
        "field, value",
        [("bed_min", "2.5"), ("bed_min", "-1"), ("bath_max", "1.3"), ("bed_max", "lots"), ("bed_max", "50")],
    )
    def test_bad_numbers(self, field, value):
        _, errors = validate_search({"state": "TX", field: value})
        assert field in errors


class TestScoring:
    def test_exact_guess_gets_max(self):
        assert score_guess(300_000, 300_000) == MAX_POINTS

    def test_score_uses_percentage_not_dollars(self):
        # $50k off a $200k home is far worse than $50k off a $5M home.
        assert score_guess(250_000, 200_000) < score_guess(5_050_000, 5_000_000)

    def test_symmetric_and_decreasing(self):
        assert score_guess(110, 100) == score_guess(90, 100)
        assert score_guess(110, 100) > score_guess(125, 100) > score_guess(200, 100) > 0

    def test_known_values(self):
        assert score_guess(110, 100) == 3352
        assert score_guess(150, 100) == 677
