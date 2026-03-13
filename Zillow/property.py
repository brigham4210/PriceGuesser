from random import choice
import re
from urllib.parse import urljoin

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
        seen = set()
        close_session()

        page_title = soup.find('title').text.strip() if soup.find('title') else ""
        if "denied" not in page_title.lower():
            print("Access granted, scraping property URLs...")

            # Primary selector used by older Zillow markup.
            property_cards = soup.find_all('a', {'data-test': 'property-card-link'})
            for card in property_cards:
                href = card.get('href')
                if not href or '/homedetails/' not in href:
                    continue
                absolute_url = urljoin('https://www.zillow.com', href)
                if absolute_url not in seen:
                    seen.add(absolute_url)
                    property_urls.append(absolute_url)

            # Fallback for updated markup where listing links live in embedded JSON.
            if not property_urls:
                html = str(soup)
                matches = re.findall(
                    r'https://www\.zillow\.com/homedetails/[^"\'\s]+|/homedetails/[^"\'\s]+',
                    html,
                )
                for href in matches:
                    absolute_url = urljoin('https://www.zillow.com', href)
                    if absolute_url not in seen:
                        seen.add(absolute_url)
                        property_urls.append(absolute_url)

        print(f"Found {len(property_urls)} property URLs")

        return property_urls

    def get_random_property_url(self):
        # Return one random property URL without relying on __str__ side effects
        property_urls = self.get_property_urls()
        if not property_urls:
            raise ValueError("No properties found for the selected criteria.")
        return choice(property_urls)

    def __str__(self):
        return self.get_random_property_url()
