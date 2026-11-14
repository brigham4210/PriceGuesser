"""Read listing links from a Zillow search results page."""
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from Zillow.cache import TTLCache
from Zillow.client import fetch

log = logging.getLogger(__name__)

SEARCH_CACHE = TTLCache(ttl_seconds=15 * 60, max_entries=200)

_BASE = "https://www.zillow.com"
_HOMEDETAILS_RE = re.compile(r"https://www\.zillow\.com/homedetails/[^\"'\s\\]+|/homedetails/[^\"'\s\\]+")


def parse_property_urls(html):
    """Return the unique listing URLs on a search page, in page order. Pure."""
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for card in soup.find_all("a", {"data-test": "property-card-link"}):
        href = card.get("href")
        if href and "/homedetails/" in href:
            urls.append(urljoin(_BASE, href))

    # Newer markup keeps listing links in embedded JSON instead of anchors.
    if not urls:
        urls = [urljoin(_BASE, href) for href in _HOMEDETAILS_RE.findall(html)]

    return list(dict.fromkeys(urls))


def fetch_property_urls(search_url, fetcher=fetch):
    """Listing URLs for a search, cached for 15 minutes."""
    cached = SEARCH_CACHE.get(search_url)
    if cached is not None:
        log.info("Using %d cached listing URLs for %s", len(cached), search_url)
        return cached

    log.info("Fetching search results from %s", search_url)
    urls = parse_property_urls(fetcher(search_url))
    log.info("Found %d listing URLs", len(urls))
    if urls:
        SEARCH_CACHE.set(search_url, urls)
    return urls
