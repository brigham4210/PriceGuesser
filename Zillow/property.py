from random import choice

from bs4 import BeautifulSoup

from Zillow import SESSION, HEADERS, close_session
from Zillow.url import TEST_URL


class Property:
    def __init__(self, website_url):
        self.url = website_url

    def get_property_urls(self):
        response = SESSION.get(self.url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        property_urls = []
        close_session()

        if soup.find('title').text != "Access to this page has been denied":
            print("Access granted, scraping property URLs...")
            property_cards = soup.find_all('a', {'data-test': 'property-card-link'})
            for card in property_cards:
                property_urls.append(card['href'])

        return property_urls

    def __str__(self):
        return choice(self.get_property_urls())


TEST_PROPERTY_URL = Property(TEST_URL)

# Example usage:
if __name__ == "__main__":
    print(TEST_PROPERTY_URL)
