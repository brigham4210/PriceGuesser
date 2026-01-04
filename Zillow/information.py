from bs4 import BeautifulSoup

from Zillow import SESSION, HEADERS, close_session
from Zillow.property import Property
from Zillow.url import Url


class Information:
    def __init__(self, url):
        # Coerce to string once to avoid repeated __str__ calls on objects like Property
        self.url = str(url)

    def get_info(self):
        print(f"Fetching property information from {self.url}")
        response = SESSION.get(self.url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        close_session()

        # Add error handling for each element
        try:
            price_elem = soup.find('span', {'data-testid': 'price'})
            price = price_elem.text if price_elem else 'Price not available'
        except AttributeError:
            price = 'Price not available'

        try:
            address_elem = soup.find('h1')
            address = address_elem.text if address_elem else 'Address not available'
        except AttributeError:
            address = 'Address not available'

        try:
            facts = soup.find_all('div', {'data-testid': 'bed-bath-sqft-fact-container'})
            beds = facts[0].text if len(facts) > 0 else 'N/A'
            baths = facts[1].text if len(facts) > 1 else 'N/A'
            sqft = facts[2].text if len(facts) > 2 else 'N/A'
        except (AttributeError, IndexError):
            beds, baths, sqft = 'N/A', 'N/A', 'N/A'

        try:
            others_container = soup.find('div', {'aria-label': "At a glance facts"})
            others = others_container.find_all('span') if others_container else []
            year_built = others[1].text if len(others) > 1 else 'N/A'
            land_area = others[2].text if len(others) > 2 else 'N/A'
        except (AttributeError, IndexError):
            year_built, land_area = 'N/A', 'N/A'

        try:
            images_container = soup.find('div', {'data-testid': "hollywood-gallery-images-tile-list"})
            images = images_container.find_all('img') if images_container else []
            image_urls = [image['src'] for image in images if image.get('src')]
        except AttributeError:
            image_urls = []

        return address, price, beds, baths, sqft, land_area, year_built, image_urls

    def __str__(self):
        info = self.get_info()
        return f"Address: {info[0]}\n{info[2]} {info[3]} {info[4]}\n{info[5]}\n{info[6]}}}"

    def get_image_urls(self):
        info = self.get_info()
        return info[7]

    def get_price(self):
        info = self.get_info()
        return info[1]
