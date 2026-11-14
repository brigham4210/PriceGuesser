import itertools

import pytest

from game import ROUNDS_PER_GAME, GameStore
from main import create_app
from Zillow import BlockedError, NoListingsError
from Zillow.listing import Listing

PRICE = 734_567


class FakeFinder:
    def __init__(self):
        self.counter = itertools.count(1)
        self.calls = []
        self.error = None

    def __call__(self, criteria, exclude=()):
        self.calls.append((criteria, set(exclude)))
        if self.error:
            raise self.error
        n = next(self.counter)
        return Listing(
            url=f"https://www.zillow.com/homedetails/{n}_zpid/",
            address=f"{n} Test St, Fresno, CA",
            price=PRICE,
            price_text=f"${PRICE:,}",
            beds="3 beds",
            image_urls=(
                "https://photos.zillowstatic.com/fp/a-cc_ft_1536.jpg",
                "https://photos.zillowstatic.com/fp/b-cc_ft_1536.jpg",
            ),
        )


@pytest.fixture
def finder():
    return FakeFinder()


@pytest.fixture
def app(finder):
    return create_app({"TESTING": True, "SECRET_KEY": "test", "FIND_LISTING": finder})


@pytest.fixture
def client(app):
    return app.test_client()


def start(client, **form):
    data = {"state": "CA"}
    data.update(form)
    return client.post("/start", data=data)


def session_cookie(client, app):
    cookie = client.get_cookie(app.config.get("SESSION_COOKIE_NAME", "session"))
    serializer = app.session_interface.get_signing_serializer(app)
    return cookie.value, serializer.loads(cookie.value)


def test_index_lists_states(client):
    html = client.get("/").get_data(as_text=True)
    assert '<option value="CA"' in html
    assert "California" in html


def test_start_redirects_to_game(client, finder):
    response = start(client, bed_min="2")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/game")
    assert finder.calls[0][0]["bed_min"] == 2
    html = client.get("/game").get_data(as_text=True)
    assert "1 Test St, Fresno, CA" in html
    assert "Round 1 of 5" in html


def test_cookie_holds_only_game_id(client, app):
    start(client)
    raw, data = session_cookie(client, app)
    assert set(data) == {"game_id"}
    assert str(PRICE) not in raw
    assert "zillow" not in raw.lower()


def test_price_and_link_hidden_before_guess(client):
    start(client)
    html = client.get("/game").get_data(as_text=True)
    assert f"{PRICE:,}" not in html
    assert "homedetails" not in html


def test_invalid_guess_shows_message(client):
    start(client)
    response = client.post("/guess", data={"guess": "a lot"})
    assert response.status_code == 400
    assert "Enter a price in dollars" in response.get_data(as_text=True)


def test_guess_reveals_price_and_points(client):
    start(client)
    client.post("/guess", data={"guess": "700k"})
    html = client.get("/game").get_data(as_text=True)
    assert f"Actual price: ${PRICE:,}" in html
    assert "too low" in html
    assert "points" in html
    assert "homedetails" in html


def test_cannot_guess_twice(client, app):
    start(client)
    client.post("/guess", data={"guess": f"{PRICE}"})
    client.post("/guess", data={"guess": "1"})
    _, data = session_cookie(client, app)
    game = app.extensions["games"].get(data["game_id"])
    assert game.current.guess == PRICE
    assert game.total_score == 5000


def test_full_game_reaches_summary(client, finder):
    start(client)
    for n in range(ROUNDS_PER_GAME):
        client.post("/guess", data={"guess": "$700,000"})
        if n < ROUNDS_PER_GAME - 1:
            assert client.post("/next").status_code == 302
    assert client.post("/next").headers["Location"].endswith("/summary")
    html = client.get("/summary").get_data(as_text=True)
    assert "Final score" in html
    assert html.count("Test St, Fresno") == ROUNDS_PER_GAME
    # Each new round excludes listings already played.
    assert finder.calls[-1][1] == {f"https://www.zillow.com/homedetails/{n}_zpid/" for n in range(1, ROUNDS_PER_GAME)}


def test_next_requires_a_guess_first(client, finder):
    start(client)
    client.post("/next")
    assert len(finder.calls) == 1


def test_summary_before_finish_redirects(client):
    start(client)
    assert client.get("/summary").headers["Location"].endswith("/game")


@pytest.mark.parametrize(
    "form, field_message",
    [
        ({"state": ""}, "Choose a state."),
        ({"state": "ZZ"}, "Choose a state from the list."),
        ({"state": "CA", "bed_min": "4", "bed_max": "2"}, "Max bedrooms can&#39;t be less than min bedrooms."),
    ],
)
def test_validation_errors(client, finder, form, field_message):
    response = client.post("/start", data=form)
    assert response.status_code == 400
    assert field_message in response.get_data(as_text=True)
    assert finder.calls == []


@pytest.mark.parametrize("error", [BlockedError("Zillow is blocking requests"), NoListingsError("No properties found")])
def test_scrape_errors_show_friendly_message(client, finder, error):
    finder.error = error
    response = start(client)
    assert response.status_code == 502
    assert str(error) in response.get_data(as_text=True)


def test_scrape_error_on_next_round_stays_on_game(client, finder):
    start(client)
    client.post("/guess", data={"guess": "700000"})
    finder.error = BlockedError("Zillow is blocking requests right now.")
    response = client.post("/next", follow_redirects=True)
    assert response.status_code == 200
    assert "Zillow is blocking requests right now." in response.get_data(as_text=True)


def test_game_without_session_redirects_home(client):
    assert client.get("/game").headers["Location"].endswith("/")


def test_reset_clears_game(client, app):
    start(client)
    client.post("/reset")
    assert len(app.extensions["games"]) == 0
    assert client.get("/game").headers["Location"].endswith("/")


def test_store_expires_games():
    now = [0.0]
    store = GameStore(ttl_seconds=60, clock=lambda: now[0])
    game_id, _ = store.create({"state": "CA"})
    assert store.get(game_id) is not None
    now[0] = 61
    assert store.get(game_id) is None
