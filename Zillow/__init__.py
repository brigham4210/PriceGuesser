"""Helpers for finding and reading Zillow listings."""


class ScrapeError(Exception):
    """Zillow could not be read. The message is safe to show to players."""


class BlockedError(ScrapeError):
    """Zillow refused the request (HTTP 403/429, a captcha, or an empty page)."""


class UnusableListing(Exception):
    """A listing page loaded but can't be played (for example, it has no sale price)."""


class NoListingsError(ScrapeError):
    """No playable listing was found for the search."""
