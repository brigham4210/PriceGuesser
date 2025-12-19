from bs4 import BeautifulSoup

from Zillow import SESSION, HEADERS, close_session
from Zillow.property import Property
from Zillow.url import Url


class Information:
    def __init__(self, url):
        # Coerce to string once to avoid repeated __str__ calls on objects like Property
        self.url = str(url)

    def get_info(self):
        print(f"Fetching information from {self.url}")

        response = SESSION.get(self.url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        close_session()

        price = soup.find('span', {'data-testid': 'price'}).text
        address = soup.find('h1').text
        facts = soup.find('div', {'data-testid': 'bed-bath-sqft-facts'}).text

        return f"Address: {address}\nPrice: {price}\nFacts: {facts}"

    def __str__(self):
        return self.get_info()


if __name__ == "__main__":
    # Get a concrete property URL string to avoid triggering Property.__str__ implicitly
    test_info = Information(Property(Url(state="in", bed_min=10, bed_max=None, bath_min=None, bath_max=None)).get_random_property_url())
    print(test_info)
