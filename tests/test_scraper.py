import random

import pytest
import requests

from conftest import fixture_html
from Zillow import BlockedError, NoListingsError, ScrapeError, UnusableListing, client, search
from Zillow.cache import TTLCache
from Zillow.information import fetch_listing, parse_listing
from Zillow.listing import Listing
from Zillow.property import fetch_property_urls, parse_property_urls

H = "0123456789abcdef0123456789abcdef"
H2 = "fedcba9876543210fedcba9876543210"


class TestParsePropertyUrls:
    def test_card_links_are_absolute_unique_and_listings_only(self):
        assert parse_property_urls(fixture_html("search_cards.html")) == [
            "https://www.zillow.com/homedetails/123-Main-St-Fresno-CA-93701/111_zpid/",
            "https://www.zillow.com/homedetails/9-Oak-Ave-Davis-CA-95616/222_zpid/",
        ]

    def test_falls_back_to_embedded_json(self):
        assert parse_property_urls(fixture_html("search_json.html")) == [
            "https://www.zillow.com/homedetails/1-Elm-St-Austin-TX-78701/333_zpid/",
            "https://www.zillow.com/homedetails/2-Pine-Rd-Dallas-TX-75201/444_zpid/",
        ]

    def test_empty_page(self):
        assert parse_property_urls("<html><body>No results</body></html>") == []


class TestParseListing:
    def test_primary_layout(self):
        listing = parse_listing(fixture_html("listing.html"), "https://z/1")
        assert listing.address == "123 Main St, Fresno, CA 93701"
        assert listing.price == 1_250_000
        assert listing.price_text == "$1,250,000"
        assert (listing.beds, listing.baths, listing.sqft) == ("3 beds", "2 baths", "1,850 sqft")
        assert listing.year_built == "Built in 1998"
        assert listing.land_area == "0.25 Acres Lot"
        assert listing.image_urls == (
            f"https://photos.zillowstatic.com/fp/{H}-cc_ft_1536.jpg",
            f"https://photos.zillowstatic.com/fp/{H2}-cc_ft_1536.jpg",
        )

    def test_alternate_layout(self):
        listing = parse_listing(fixture_html("listing_alt.html"), "https://z/2")
        assert listing.price == 2_100_000
        assert (listing.beds, listing.baths, listing.sqft) == ("4 bd", "3.5 ba", "3,100 sqft")
        assert listing.year_built == "Built in 2015"
        assert listing.image_urls == (f"https://photos.zillowstatic.com/fp/{H2}-cc_ft_1536.jpg",)

    def test_rental_has_no_price(self):
        listing = parse_listing(fixture_html("listing_rental.html"), "https://z/3")
        assert listing.price is None
        assert listing.price_text == "$2,400/mo"


class TestFetchListing:
    def test_rental_is_unusable(self):
        with pytest.raises(UnusableListing):
            fetch_listing("https://z/3", fetcher=lambda url: fixture_html("listing_rental.html"))

    def test_page_without_price_or_address_counts_as_blocked(self):
        with pytest.raises(BlockedError):
            fetch_listing("https://z/4", fetcher=lambda url: "<html><body></body></html>")

    def test_results_are_cached(self):
        calls = []

        def fetcher(url):
            calls.append(url)
            return fixture_html("listing.html")

        first = fetch_listing("https://z/1", fetcher=fetcher)
        second = fetch_listing("https://z/1", fetcher=fetcher)
        assert first is second
        assert calls == ["https://z/1"]

    def test_search_results_are_cached(self):
        calls = []

        def fetcher(url):
            calls.append(url)
            return fixture_html("search_cards.html")

        assert fetch_property_urls("https://z/s", fetcher=fetcher) == fetch_property_urls(
            "https://z/s", fetcher=fetcher
        )
        assert calls == ["https://z/s"]


class FakeResponse:
    def __init__(self, status=200, text="<html><title>ok</title></html>"):
        self.status_code = status
        self.text = text


class FakeSession:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def get(self, url, headers=None, timeout=None):
        self.calls.append(timeout)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class TestFetch:
    def test_success_uses_timeout(self):
        session = FakeSession(FakeResponse(text="<html><title>Home</title>hello</html>"))
        assert "hello" in client.fetch("u", session=session, sleep=lambda s: None)
        assert session.calls == [client.TIMEOUT_SECONDS]

    @pytest.mark.parametrize("status", [403, 429])
    def test_refused_status_is_blocked(self, status):
        with pytest.raises(BlockedError):
            client.fetch("u", session=FakeSession(FakeResponse(status)), sleep=lambda s: None)

    def test_captcha_page_is_blocked(self):
        session = FakeSession(FakeResponse(text=fixture_html("blocked.html")))
        with pytest.raises(BlockedError):
            client.fetch("u", session=session, sleep=lambda s: None)

    def test_retries_server_errors_then_succeeds(self):
        session = FakeSession(FakeResponse(503), FakeResponse(text="<html>ok</html>"))
        assert client.fetch("u", session=session, sleep=lambda s: None) == "<html>ok</html>"
        assert len(session.calls) == 2

    def test_retries_are_limited(self):
        session = FakeSession(*[requests.Timeout("slow")] * 5)
        with pytest.raises(ScrapeError) as info:
            client.fetch("u", session=session, sleep=lambda s: None)
        assert not isinstance(info.value, BlockedError)
        assert len(session.calls) == client.MAX_ATTEMPTS

    def test_other_status_is_an_error(self):
        with pytest.raises(ScrapeError):
            client.fetch("u", session=FakeSession(FakeResponse(404)), sleep=lambda s: None)


def make_listing(url, price=500_000):
    return Listing(url=url, address=f"Home at {url}", price=price, price_text=f"${price:,}")


class TestFindListing:
    def setup_method(self):
        self.search_calls = []
        self.listing_calls = []

    def install(self, monkeypatch, results, unusable=()):
        def fake_urls(search_url):
            self.search_calls.append(search_url)
            for key, urls in results.items():
                if key(search_url):
                    return urls
            return []

        def fake_listing(url):
            self.listing_calls.append(url)
            if url in unusable:
                raise UnusableListing(url)
            return make_listing(url)

        monkeypatch.setattr(search, "fetch_property_urls", fake_urls)
        monkeypatch.setattr(search, "fetch_listing", fake_listing)

    def test_skips_listings_without_a_price(self, monkeypatch):
        self.install(monkeypatch, {lambda u: True: ["a", "b"]}, unusable={"a"})
        listing = search.find_listing({"state": "CA"}, rng=random.Random(0))
        assert listing.url == "b"

    def test_excludes_seen_listings(self, monkeypatch):
        self.install(monkeypatch, {lambda u: True: ["a", "b", "c"]})
        listing = search.find_listing({"state": "CA"}, exclude={"a", "b"})
        assert listing.url == "c"
        assert self.listing_calls == ["c"]

    def test_relaxes_filters_when_nothing_matches(self, monkeypatch):
        self.install(monkeypatch, {lambda u: "%22min%22%3A%205" not in u: ["broad"]})
        criteria = {"state": "CA", "bed_min": 5, "bed_max": None, "bath_min": None, "bath_max": None}
        listing = search.find_listing(criteria)
        assert listing.url == "broad"
        assert len(self.search_calls) == 2

    def test_no_listings(self, monkeypatch):
        self.install(monkeypatch, {})
        with pytest.raises(NoListingsError):
            search.find_listing({"state": "WY", "bed_min": 1, "bed_max": None, "bath_min": None, "bath_max": None})

    def test_blocked_stops_immediately(self, monkeypatch):
        def blocked(url):
            raise BlockedError("blocked")

        monkeypatch.setattr(search, "fetch_property_urls", blocked)
        with pytest.raises(BlockedError):
            search.find_listing({"state": "CA", "bed_min": 1, "bed_max": None, "bath_min": None, "bath_max": None})


class TestTTLCache:
    def test_expiry_and_size_limit(self):
        now = [0.0]
        cache = TTLCache(ttl_seconds=10, max_entries=2, clock=lambda: now[0])
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        assert cache.get("a") is None
        assert cache.get("b") == 2
        now[0] = 11
        assert cache.get("b") is None
