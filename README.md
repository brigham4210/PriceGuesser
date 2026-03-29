# 🏠 PriceGuesser

An interactive web-based game where you guess real estate property prices using actual Zillow listings. Challenge yourself to predict property values based on property details like location, bedrooms, bathrooms, and square footage!

## 📋 Overview

PriceGuesser is a Flask web application that scrapes live Zillow property listings and presents them to users for price guessing. Players can filter properties by state and bedroom/bathroom ranges, then make predictions about property values. The app reveals the actual price and shows how close their guess was.

## 🎮 How It Works

1. **Enter Search Criteria** - Specify a state and optional bedroom/bathroom ranges
2. **Generate Property** - App fetches a random Zillow listing matching your filters
3. **View Property Details** - See photos, address, beds, baths, sqft, land area, and year built
4. **Make Your Guess** - Enter your predicted property price
5. **See Results** - Reveal the actual price and view your difference (±$)
6. **Play Again** - Generate another property or modify your search criteria

## ✨ Features

- **Property Filtering** - Search by state with optional bedroom and bathroom range filters
- **Smart Fallback** - If specific criteria yields no results, automatically relaxes filters to find properties by state
- **Live Zillow Data** - Real property information scraped directly from Zillow
- **Property Images** - View actual listing photos
- **Session Management** - Game state persists across page navigation
- **Error Handling** - Graceful handling of unavailable properties and scraping issues
- **Responsive Design** - Clean, styled interface that works across devices

## 🛠️ Tech Stack

- **Backend**: Flask (Python web framework)
- **Web Scraping**: BeautifulSoup, Requests library
- **Frontend**: HTML5, CSS3
- **State Management**: Flask session management

## 📁 Project Structure

```
PriceGuesser/
├── main.py                    # Flask app & route handlers
├── README.md                  # This file
├── static/                    # Static assets (CSS, images, favicon)
├── templates/
│   ├── index.html            # Search criteria form page
│   └── game.html             # Game interface & guessing page
└── Zillow/
    ├── __init__.py           # Session & request headers config
    ├── url.py                # Build Zillow search URLs
    ├── property.py           # Fetch random properties from search results
    └── information.py        # Scrape property details & images from listing page
```

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- Flask
- BeautifulSoup4
- Requests

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd PriceGuesser
```

2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies
```bash
pip install flask beautifulsoup4 requests
```

4. Run the application
```bash
python main.py
```

5. Open your browser and navigate to `http://localhost:5000`

## 🌐 API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home page with search form |
| `/generate` | POST | Process search criteria and fetch a property |
| `/game` | GET | Display property with guessing interface |
| `/guess` | POST | Submit price guess |
| `/generate_again` | GET | Fetch another property with same search criteria |

## 📝 Example Usage

1. Go to the homepage
2. Enter state abbreviation (e.g., "CA", "NY", "TX")
3. Optionally specify bedroom and bathroom ranges
4. Click "Find Property"
5. View the property details and images
6. Enter your price guess in the format: `$500000` or `500000`
7. Click "Guess Price" to reveal the actual price
8. Click "Another Property" to search again or go back to modify criteria

## 🔍 How Web Scraping Works

The app uses BeautifulSoup to:
- **Zillow Search URLs** - Generate search URLs based on user filters
- **Property Listings** - Extract property URLs from Zillow search results
- **Property Information** - Scrape property details (price, address, beds, baths, sqft, land area, year built) and image URLs from individual listing pages

## ⚠️ Notes

- Zillow may occasionally block requests; the app includes fallback mechanisms
- Property data is fetched in real-time, so listings may no longer be available
- Game generates random properties from search results for variety

## 📄 License

[Add your license here]
