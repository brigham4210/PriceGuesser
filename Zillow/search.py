"""Pick a random playable listing for a set of search criteria."""
import logging
import random

from Zillow import NoListingsError, UnusableListing
from Zillow.information import fetch_listing
from Zillow.property import fetch_property_urls
from Zillow.url import Url

log = logging.getLogger(__name__)

# How many listing pages to try per search before giving up on it.
MAX_LISTING_TRIES = 3

NO_LISTINGS_MESSAGE = "No properties found for your filters or a broader search of that state. Try another state."


def _searches(criteria):
    yield criteria
    relaxed = {"state": criteria["state"]}
    if any(criteria.get(k) is not None for k in ("bed_min", "bed_max", "bath_min", "bath_max")):
        yield relaxed


def find_listing(criteria, exclude=(), rng=random):
    """Return a Listing matching `criteria` whose URL is not in `exclude`.

    Tries the exact filters first, then the whole state. Listings without a
    usable sale price are skipped. BlockedError and ScrapeError propagate so
    we stop hitting Zillow as soon as it refuses us.
    """
    exclude = set(exclude)
    for search in _searches(criteria):
        url = str(Url(**search))
        candidates = [u for u in fetch_property_urls(url) if u not in exclude]
        rng.shuffle(candidates)
        for listing_url in candidates[:MAX_LISTING_TRIES]:
            try:
                return fetch_listing(listing_url)
            except UnusableListing:
                continue
        log.info("No playable listing for %s", search)
    raise NoListingsError(NO_LISTINGS_MESSAGE)


def clear_caches():
    from Zillow.information import LISTING_CACHE
    from Zillow.property import SEARCH_CACHE

    LISTING_CACHE.clear()
    SEARCH_CACHE.clear()
