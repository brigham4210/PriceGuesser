import requests

SESSION = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 Chrome/120.0.0.0",
    "Accept-Language": "en",
    "Accept": "text/html",
}


def close_session():
    SESSION.close()
