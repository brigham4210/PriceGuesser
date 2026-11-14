"""Read one Zillow listing page into a Listing."""

import logging
import re

from bs4 import BeautifulSoup

from Zillow import BlockedError, UnusableListing
from Zillow.cache import TTLCache
from Zillow.client import BLOCKED_MESSAGE, fetch
from Zillow.listing import Listing, parse_price

log = logging.getLogger(__name__)

LISTING_CACHE = TTLCache(ttl_seconds=60 * 60, max_entries=500)

_ACRES_RE = re.compile(r"\b(Acres|Acre)\b", re.IGNORECASE)
_SQFT_RE = re.compile(r"\bsqft\b", re.IGNORECASE)
_IMAGE_PATTERNS = (
    re.compile(r"https://photos\.zillowstatic\.com/fp/[a-f0-9]+-uncropped_scaled_within_1536_1152\.webp"),
    re.compile(r"https://photos\.zillowstatic\.com/fp/[a-f0-9]+-cc_ft_1536\.jpg"),
)
_PHOTO_HASH_RE = re.compile(r"https://photos\.zillowstatic\.com/fp/([a-f0-9]{32})-")


def _text(elem):
    return elem.get_text(strip=True) if elem else ""


def _address(soup):
    elem = soup.find("h1")
    if not elem:
        return ""
    # Zillow splits the street and city into child elements; keep a space between them.
    text = " ".join(elem.get_text(" ", strip=True).split())
    return re.sub(r"\s*,\s*", ", ", text)


def _price_text(soup):
    elem = soup.find("span", {"data-testid": "price"}) or soup.find("span", class_="price-text")
    return _text(elem)


def _bed_bath_sqft(soup):
    beds = baths = sqft = "N/A"
    for container in soup.find_all("div", {"data-testid": "bed-bath-sqft-fact-container"}):
        spans = container.find_all("span")
        if len(spans) < 2:
            continue
        value, label = spans[0].get_text(strip=True), spans[1].get_text(strip=True)
        lower = label.lower()
        if "bed" in lower:
            beds = f"{value} {label}"
        elif "bath" in lower:
            baths = f"{value} {label}"
        elif "sqft" in lower:
            sqft = f"{value} {label}"

    if beds == baths == sqft == "N/A":
        values = soup.find_all("span", {"data-testid": "bed-bath-sqft-text__value"})
        labels = soup.find_all("span", {"data-testid": "bed-bath-sqft-text__description"})
        if len(values) >= 3 and len(labels) >= 3:
            pairs = zip(values[:3], labels[:3], strict=True)
            beds, baths, sqft = (f"{_text(v)} {_text(d)}" for v, d in pairs)
    return beds, baths, sqft


def _year_and_land(soup):
    year_built = land_area = "N/A"
    acres = soup.find("span", string=_ACRES_RE)
    if acres:
        land_area = acres.get_text(strip=True)

    glance = soup.find("div", {"data-testid": "at-a-glance"}) or soup.find("div", {"aria-label": "At a glance facts"})
    if glance:
        for span in glance.find_all("span"):
            text = span.get_text(strip=True)
            if not text:
                continue
            lower = text.lower()
            if "built in" in lower:
                year_built = text
            elif (_ACRES_RE.search(text) or _SQFT_RE.search(text)) and not any(
                word in lower for word in ("price", "zestimate", "/sqft")
            ):
                land_area = text
    return year_built, land_area


def _image_urls(html):
    for pattern in _IMAGE_PATTERNS:
        urls = list(dict.fromkeys(pattern.findall(html)))
        if urls:
            return tuple(urls)
    hashes = dict.fromkeys(_PHOTO_HASH_RE.findall(html))
    return tuple(f"https://photos.zillowstatic.com/fp/{h}-cc_ft_1536.jpg" for h in hashes)


def parse_listing(html, url):
    """Parse a listing page. Pure: no network access."""
    soup = BeautifulSoup(html, "html.parser")
    price_text = _price_text(soup)
    address = _address(soup)
    beds, baths, sqft = _bed_bath_sqft(soup)
    year_built, land_area = _year_and_land(soup)
    return Listing(
        url=url,
        address=address or "Address not available",
        price=parse_price(price_text),
        price_text=price_text or "Price not available",
        beds=beds,
        baths=baths,
        sqft=sqft,
        land_area=land_area,
        year_built=year_built,
        image_urls=_image_urls(html),
    )


def fetch_listing(url, fetcher=fetch):
    """Fetch and parse a listing, using the cache when possible.

    Raises BlockedError when the page has neither a price nor an address
    (Zillow served something other than the listing) and UnusableListing
    when the listing has no sale price to guess.
    """
    cached = LISTING_CACHE.get(url)
    if cached is not None:
        return cached

    log.info("Fetching listing %s", url)
    listing = parse_listing(fetcher(url), url)
    if listing.price is None and listing.address == "Address not available":
        log.warning("Listing page %s had no price or address; treating it as blocked", url)
        raise BlockedError(BLOCKED_MESSAGE)
    if listing.price is None:
        log.info("Skipping %s: no usable sale price (%r)", url, listing.price_text)
        raise UnusableListing(url)

    log.info("Found %d images for %s", len(listing.image_urls), url)
    LISTING_CACHE.set(url, listing)
    return listing
