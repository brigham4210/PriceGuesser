# 🏠 PriceGuesser

An interactive web game where you guess the prices of real Zillow listings. Each game is 5 rounds; the closer your guess, the more points you score.

## 📋 Overview

PriceGuesser is a Flask web application that scrapes live Zillow listings and presents them for price guessing. Players pick a state and optional bedroom/bathroom ranges, then guess each property's price. After each guess the app reveals the actual price, how far off you were, and your points for the round.

## 🎮 How It Works

1. **Pick a state** - Choose a state and, optionally, bedroom and bathroom ranges
2. **View the property** - See photos, address, beds, baths, sqft, land area, and year built
3. **Make your guess** - Type a price like `$450,000`, `450000` or `450k`
4. **See the result** - The actual price, how far off you were, and your points (up to 5,000)
5. **Play 5 rounds** - Then see your final score out of 25,000 and your best score in this browser

### Scoring

Points depend on how far off you were as a percentage of the price, so $50k off a $200k home costs more than $50k off a $5M home:

| Off by | Points |
|--------|--------|
| 0% | 5,000 |
| 1% | 4,804 |
| 10% | 3,352 |
| 25% | 1,839 |
| 50% | 677 |

## ✨ Features

- **Property filtering** - Search by state with optional bedroom and bathroom ranges, checked on the server
- **Smart fallback** - If your filters find nothing, the app searches the whole state; listings without a sale price (rentals, missing prices) are skipped
- **Fair play** - Prices are kept on the server. The session cookie holds only a random game ID
- **Caching** - Search results are cached for 15 minutes and listings for 1 hour, so later rounds make one request to Zillow instead of two
- **Safe failures** - Timeouts, limited retries, and detection of Zillow's block pages. Errors show a message instead of a crash
- **Photo carousel** - Browse listing photos with buttons or the arrow keys

## 🛠️ Tech Stack

- **Backend**: Flask
- **Web scraping**: BeautifulSoup, Requests
- **Frontend**: HTML, CSS, a little JavaScript
- **Tests**: pytest, run on GitHub Actions

## 📁 Project Structure

```
PriceGuesser/
├── main.py                 # Flask app factory and routes
├── game.py                 # Game, rounds, scoring, server-side game store
├── forms.py                # Search form and guess validation, state list
├── requirements.txt        # Pinned runtime dependencies
├── requirements-dev.txt    # Adds pytest
├── static/
│   ├── css/style.css
│   ├── js/game.js          # Guess formatting, photo carousel, best score
│   └── favicon.svg
├── templates/
│   ├── base.html
│   ├── index.html          # Search form
│   ├── game.html           # Guessing and results
│   └── summary.html        # Final score
├── Zillow/
│   ├── __init__.py         # Error types
│   ├── client.py           # HTTP: timeouts, retries, block detection
│   ├── cache.py            # In-memory TTL cache
│   ├── url.py              # Build Zillow search URLs
│   ├── property.py         # Listing links from search results
│   ├── information.py      # Listing details from a listing page
│   ├── listing.py          # Listing record and price parsing
│   └── search.py           # Pick a random playable listing
└── tests/                  # pytest suite with saved HTML fixtures
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+

### Installation

1. Clone the repository
```bash
git clone https://github.com/brigham4210/PriceGuesser.git
cd PriceGuesser
```

2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run the application
```bash
python main.py
```

5. Open `http://localhost:5000`

### Configuration

Set these environment variables as needed:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | random per start | Signs the session cookie. Without it, every player's session resets when the server restarts |
| `FLASK_DEBUG` | off | Set to `1` to run with the debugger and auto-reload |
| `LOG_LEVEL` | `INFO` | Logging level, for example `DEBUG` or `WARNING` |

### Running tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests never call Zillow. Scraper tests use small HTML fixtures in `tests/fixtures/` that mirror the parts of Zillow's markup the parser reads.

## 🌐 Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Search form |
| `/start` | POST | Validate the search and start a 5-round game |
| `/game` | GET | Current round |
| `/guess` | POST | Submit a guess for the current round |
| `/next` | POST | Load the next round |
| `/summary` | GET | Final score after round 5 |
| `/reset` | POST | End the game and go back to the search form |

## ⚠️ Notes

- Games are kept in the server's memory. They are lost on restart and aren't shared between worker processes, so run a single process (the default for `python main.py`).
- Zillow may block requests at any time; when it does, the app says so and asks you to try again later.
- Zillow's terms of service may not allow scraping. This project is for personal and educational use.

## 📄 License

Released under the [MIT License](LICENSE).
