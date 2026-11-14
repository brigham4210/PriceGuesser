import logging
import os
import secrets

from flask import Flask, flash, redirect, render_template, request, session, url_for

from forms import STATES, parse_guess, validate_search
from game import MAX_POINTS, ROUNDS_PER_GAME, GameStore
from Zillow import ScrapeError
from Zillow.search import find_listing

log = logging.getLogger(__name__)

EMPTY_FORM = {"state": "", "bed_min": "", "bed_max": "", "bath_min": "", "bath_max": ""}


def create_app(config=None):
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app = Flask(__name__)

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        log.warning("SECRET_KEY is not set; using a random key, so sessions reset when the server restarts.")
        secret_key = secrets.token_hex(32)
    app.config.update(SECRET_KEY=secret_key, FIND_LISTING=find_listing)
    if config:
        app.config.update(config)

    games = GameStore()
    app.extensions["games"] = games

    def current_game():
        return games.get(session.get("game_id"))

    def form_values(criteria):
        return {k: "" if criteria.get(k) is None else str(criteria[k]) for k in EMPTY_FORM}

    def render_index(values=None, errors=None, error=None, status=200):
        return render_template(
            "index.html",
            states=STATES,
            rounds_per_game=ROUNDS_PER_GAME,
            values=values or EMPTY_FORM,
            errors=errors or {},
            error=error,
        ), status

    def render_game(game, guess_error=None, status=200):
        return render_template(
            "game.html",
            game=game,
            round=game.current,
            rounds_per_game=ROUNDS_PER_GAME,
            max_points=MAX_POINTS,
            guess_error=guess_error,
        ), status

    @app.route("/")
    def index():
        game = current_game()
        return render_index(values=form_values(game.criteria) if game else None)

    @app.route("/start", methods=["POST"])
    def start():
        criteria, errors = validate_search(request.form)
        if errors:
            values = {k: request.form.get(k, "") for k in EMPTY_FORM}
            return render_index(values=values, errors=errors, status=400)

        old_id = session.pop("game_id", None)
        if old_id:
            games.delete(old_id)

        try:
            listing = app.config["FIND_LISTING"](criteria)
        except ScrapeError as err:
            return render_index(values=form_values(criteria), error=str(err), status=502)

        game_id, game = games.create(criteria)
        game.add_round(listing)
        session.clear()
        session["game_id"] = game_id
        return redirect(url_for("play"))

    @app.route("/game")
    def play():
        game = current_game()
        if game is None or game.current is None:
            return redirect(url_for("index"))
        return render_game(game)

    @app.route("/guess", methods=["POST"])
    def guess():
        game = current_game()
        if game is None or game.current is None:
            return redirect(url_for("index"))
        if game.current.guessed:
            return redirect(url_for("play"))

        value = parse_guess(request.form.get("guess"))
        if value is None:
            return render_game(game, guess_error="Enter a price in dollars, like $450,000 or 450k.", status=400)
        game.record_guess(value)
        return redirect(url_for("play"))

    @app.route("/next", methods=["POST"])
    def next_round():
        game = current_game()
        if game is None or game.current is None:
            return redirect(url_for("index"))
        if game.finished:
            return redirect(url_for("summary"))
        if not game.current.guessed:
            return redirect(url_for("play"))

        try:
            listing = app.config["FIND_LISTING"](game.criteria, exclude=game.seen_urls)
        except ScrapeError as err:
            flash(str(err))
            return redirect(url_for("play"))
        game.add_round(listing)
        return redirect(url_for("play"))

    @app.route("/summary")
    def summary():
        game = current_game()
        if game is None or not game.finished:
            return redirect(url_for("play"))
        return render_template(
            "summary.html",
            game=game,
            rounds_per_game=ROUNDS_PER_GAME,
            max_total=MAX_POINTS * ROUNDS_PER_GAME,
        )

    @app.route("/reset", methods=["POST"])
    def reset():
        game_id = session.pop("game_id", None)
        if game_id:
            games.delete(game_id)
        session.clear()
        return redirect(url_for("index"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
