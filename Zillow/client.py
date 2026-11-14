"""HTTP access to Zillow with timeouts, limited retries and block detection."""

import logging
import re
import time

import requests

from Zillow import BlockedError, ScrapeError

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 Chrome/120.0.0.0",
    "Accept-Language": "en",
    "Accept": "text/html",
}
TIMEOUT_SECONDS = 10
MAX_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 0.5

# Markers of Zillow's bot wall (PerimeterX "press and hold" captcha).
_BLOCK_MARKERS = ("px-captcha", "press &amp; hold", "press & hold")
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

BLOCKED_MESSAGE = "Zillow is blocking requests from this server right now. Wait a few minutes and try again."
UNREACHABLE_MESSAGE = "Couldn't reach Zillow. Check your connection and try again."

_session = requests.Session()


def looks_blocked(html):
    lower = html.lower()
    match = _TITLE_RE.search(html)
    title = match.group(1).lower() if match else ""
    if "denied" in title or "captcha" in title:
        return True
    return any(marker in lower for marker in _BLOCK_MARKERS)


def fetch(url, session=None, sleep=time.sleep):
    """Return the page HTML, or raise ScrapeError / BlockedError."""
    session = session or _session
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = session.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
        except requests.RequestException as err:
            log.warning("Request to %s failed (attempt %d/%d): %s", url, attempt, MAX_ATTEMPTS, err)
        else:
            status = response.status_code
            if status in (403, 429):
                log.warning("Zillow returned HTTP %d for %s", status, url)
                raise BlockedError(BLOCKED_MESSAGE)
            if status >= 500:
                log.warning("Zillow returned HTTP %d for %s (attempt %d/%d)", status, url, attempt, MAX_ATTEMPTS)
            elif status != 200:
                log.warning("Zillow returned HTTP %d for %s", status, url)
                raise ScrapeError(f"Zillow returned an unexpected response (HTTP {status}). Try again.")
            elif looks_blocked(response.text):
                log.warning("Zillow served a captcha or access-denied page for %s", url)
                raise BlockedError(BLOCKED_MESSAGE)
            else:
                return response.text
        if attempt < MAX_ATTEMPTS:
            sleep(RETRY_DELAY_SECONDS * attempt)
    raise ScrapeError(UNREACHABLE_MESSAGE)
