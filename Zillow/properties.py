from random import choice

import requests
from bs4 import BeautifulSoup

from Zillow.url import TEST_URL


class Properties:
    def __init__(self, website_url):
        self.url = website_url
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 Chrome/120.0.0.0",
            "Accept-Language": "en",
            "Accept": "text/html",
        }

    def close_session(self):
        self.session.close()

    def property_urls(self):

        response = self.session.get(self.url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        property_urls = []
        self.close_session()

        if soup.find('title').text != "Access to this page has been denied":
            print("Access granted, scraping property URLs...")
            property_cards = soup.find_all('a', {'data-test': 'property-card-link'})
            for card in property_cards:
                property_urls.append(card['href'])

        return property_urls

    def __str__(self):
        return choice(self.property_urls())


# Example usage:
if __name__ == "__main__":
    print(Properties(TEST_URL))
