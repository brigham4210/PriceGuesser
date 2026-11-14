from pathlib import Path

import pytest

from Zillow.search import clear_caches

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_html(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _fresh_caches():
    clear_caches()
    yield
    clear_caches()
