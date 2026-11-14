"""Game state, scoring, and the server-side store that keeps answers out of cookies."""

from __future__ import annotations

import math
import secrets
import threading
import time
from dataclasses import dataclass, field

from Zillow.listing import Listing

ROUNDS_PER_GAME = 5
MAX_POINTS = 5000
# Points fall off exponentially with percentage error:
# 1% off -> 4804, 10% off -> 3352, 25% off -> 1839, 50% off -> 677.
SCORE_DECAY = 4


def percent_error(guess, actual):
    return abs(guess - actual) / actual


def score_guess(guess, actual):
    return round(MAX_POINTS * math.exp(-SCORE_DECAY * percent_error(guess, actual)))


@dataclass
class Round:
    listing: Listing
    guess: int | None = None
    points: int | None = None

    @property
    def guessed(self):
        return self.guess is not None

    @property
    def difference(self):
        return None if self.guess is None else self.guess - self.listing.price

    @property
    def percent_off(self):
        return None if self.guess is None else percent_error(self.guess, self.listing.price) * 100


@dataclass
class Game:
    criteria: dict
    rounds: list = field(default_factory=list)

    @property
    def current(self):
        return self.rounds[-1] if self.rounds else None

    @property
    def round_number(self):
        return len(self.rounds)

    @property
    def total_score(self):
        return sum(r.points or 0 for r in self.rounds)

    @property
    def finished(self):
        return len(self.rounds) >= ROUNDS_PER_GAME and self.current.guessed

    @property
    def seen_urls(self):
        return {r.listing.url for r in self.rounds}

    def add_round(self, listing):
        if self.current and not self.current.guessed:
            raise ValueError("The current round hasn't been guessed yet.")
        if len(self.rounds) >= ROUNDS_PER_GAME:
            raise ValueError("The game is over.")
        self.rounds.append(Round(listing))

    def record_guess(self, guess):
        current = self.current
        if current is None or current.guessed:
            raise ValueError("There is no round waiting for a guess.")
        current.guess = guess
        current.points = score_guess(guess, current.listing.price)
        return current


class GameStore:
    """Games kept in server memory, keyed by a random ID.

    Only the ID goes in the session cookie, so players can't read prices
    from it. Games live in this process only: they are lost on restart and
    not shared between worker processes.
    """

    def __init__(self, ttl_seconds=2 * 60 * 60, max_games=1000, clock=time.monotonic):
        self.ttl = ttl_seconds
        self.max_games = max_games
        self._clock = clock
        self._games = {}
        self._lock = threading.Lock()

    def _prune(self, now):
        expired = [gid for gid, (touched, _) in self._games.items() if now - touched > self.ttl]
        for gid in expired:
            del self._games[gid]
        while len(self._games) >= self.max_games:
            oldest = min(self._games, key=lambda gid: self._games[gid][0])
            del self._games[oldest]

    def create(self, criteria):
        game = Game(criteria=dict(criteria))
        game_id = secrets.token_urlsafe(16)
        with self._lock:
            now = self._clock()
            self._prune(now)
            self._games[game_id] = (now, game)
        return game_id, game

    def get(self, game_id):
        if not game_id:
            return None
        with self._lock:
            item = self._games.get(game_id)
            if item is None:
                return None
            now = self._clock()
            if now - item[0] > self.ttl:
                del self._games[game_id]
                return None
            self._games[game_id] = (now, item[1])
            return item[1]

    def delete(self, game_id):
        with self._lock:
            self._games.pop(game_id, None)

    def __len__(self):
        with self._lock:
            return len(self._games)
