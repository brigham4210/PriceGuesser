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

        price = soup.find('span', {'data-testid': 'price'}).text
        address = soup.find('h1').text
        facts = soup.find_all('div', {'data-testid': 'bed-bath-sqft-fact-container'})
        beds = facts[0].text
        baths = facts[1].text
        sqft = facts[2].text
        others = soup.find('div', {'aria-label': "At a glance facts"}).find_all('span')
        year_built = others[1].text
        land_area = others[2].text

        images = soup.find('div', {'data-testid': "hollywood-gallery-images-tile-list"}).find_all('img')
        image_urls = [image['src'] for image in images]

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
