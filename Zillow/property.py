from random import choice

from bs4 import BeautifulSoup

from Zillow import SESSION, HEADERS, close_session


class Property:
    def __init__(self, website_url):
        self.url = str(website_url)

    def get_property_urls(self):
        print(f"Fetching Website URLs from {self.url}")
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

    def get_random_property_url(self):
        # Return one random property URL without relying on __str__ side effects
        return choice(self.get_property_urls())

    def __str__(self):
        return choice(self.get_property_urls())
