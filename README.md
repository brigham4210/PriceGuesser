# 🏠 PriceGuesser

An interactive web game where you guess the prices of real Zillow listings. Each game is 5 rounds; the closer your guess, the more points you score.

## 📋 Overview

PriceGuesser is a Flask web application that scrapes live Zillow listings and presents them for price guessing. Players pick a state and optional bedroom/bathroom ranges, then guess each property's price. After each guess the app reveals the actual price, how far off you were, and your points for the round.

## 📱 Android App

Download `PriceGuesser-<version>.apk` from the [latest release](https://github.com/brigham4210/PriceGuesser/releases/latest), open it on your phone and allow installs from your browser or file manager if Android asks. Requires Android 7.0 or newer on a 64-bit device.

The app runs the same Flask game on the phone itself, using [Chaquopy](https://chaquo.com/chaquopy/) for Python, and shows it in a WebView. Nothing is hosted: the phone requests Zillow directly, and Zillow links open in your browser.

## 🍎 iOS App (sideload)

Each release also has an unsigned `PriceGuesser-<version>.ipa` for personal use. iPhones only run signed apps, so you sign it with your own free Apple ID using a sideloading tool on a Windows PC or Mac:

1. Install [Sideloadly](https://sideloadly.io/) or [AltStore](https://altstore.io/) on your computer.
2. Connect your iPhone, open the `.ipa` in the tool and sign in with your Apple ID.
3. On the iPhone, open **Settings → General → VPN & Device Management**, trust your Apple ID, and turn on **Developer Mode** (Settings → Privacy & Security) if iOS asks.

With a free Apple ID the app stops opening after 7 days until you sideload it again. AltStore can refresh it automatically over Wi-Fi.

The iOS app is built with [Briefcase](https://briefcase.beeware.org/) and [Toga](https://toga.beeware.org/). Like the Android app, it runs the same Flask game on the phone and shows it in a web view.

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
- **Android**: Java WebView shell, Chaquopy (Python 3.12 on Android)
- **iOS**: Briefcase and Toga (Python 3.13 on iOS)
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
├── tests/                  # pytest suite with saved HTML fixtures
├── android/                # Android app (Gradle project)
│   └── app/src/main/
│       ├── java/.../MainActivity.java   # WebView, starts the server
│       └── python/android_server.py     # Runs the Flask app on 127.0.0.1
└── ios/                    # iOS app (Briefcase project)
    ├── pyproject.toml      # Briefcase config
    ├── sync_webapp.sh      # Copies the Flask game into src/pgweb
    └── src/priceguesser/app.py          # Toga web view, starts the server
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

### Building the Android app

The Gradle build copies `main.py`, `game.py`, `forms.py`, `Zillow/`, `templates/` and `static/` into the app, so the app always matches the web version. You need JDK 17, the Android SDK, Python 3.12 (Chaquopy uses it at build time) and Gradle 8.14, or open `android/` in Android Studio.

```bash
gradle -p android assembleDebug
```

The APK is written to `android/app/build/outputs/apk/debug/app-debug.apk`.

### Building the iOS app

This needs a Mac with Xcode and Python 3.13:

```bash
pip install briefcase==0.4.7
```

```bash
cd ios && ./sync_webapp.sh && briefcase run iOS
```

That runs the app in the iOS simulator. CI builds the unsigned `.ipa` with `xcodebuild` for `iphoneos` with code signing turned off.

### Releases

GitHub Actions builds the APK and IPA on every push, launches each in an emulator or simulator to check that the game loads, and attaches both to a GitHub release when you push a `v*` tag:

```bash
git tag v1.2.0 && git push origin v1.2.0
```

Releases are signed with a release key when the repository has the secrets `ANDROID_KEYSTORE_BASE64` (a base64 PKCS12 keystore), `ANDROID_KEYSTORE_PASSWORD` and `ANDROID_KEY_ALIAS`. Without them, CI builds a debug-signed APK. Each debug build has a different key, so updating means uninstalling first.

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
