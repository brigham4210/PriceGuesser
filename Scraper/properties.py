import requests
from bs4 import BeautifulSoup

from Scraper.url import TEST_URL


class Properties:
    def __init__(self, website_url):
        self.url = website_url
        self.session = requests.Session()

    def property_urls(self):
        headers = {
            "User-Agent": "Mozilla/5.0 Chrome/120.0.0.0",
            "Accept-Language": "en",
            "Accept": "text/html",
        }
        response = self.session.get(self.url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        property_urls = []

        if soup.find('title').text != "Access to this page has been denied":
            print("Access granted, scraping property URLs...")
            property_cards = soup.find_all('a', {'data-test': 'property-card-link'})
            for card in property_cards:
                property_urls.append(card['href'])

        return property_urls


if __name__ == "__main__":
    properties = Properties(TEST_URL)
    urls = properties.property_urls()
    for url in urls:
        print(url)
