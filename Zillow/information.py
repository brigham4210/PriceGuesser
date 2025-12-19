from bs4 import BeautifulSoup

from Zillow import SESSION, HEADERS, close_session
from Zillow.property import TEST_PROPERTY_URL


class Information:
    def __init__(self, url):
        self.url = url

    def get_info(self):
        print(f"Fetching information from {self.url}")

        response = SESSION.get(self.url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        close_session()

        price = soup.find('span', {'data-testid': 'price'}).text
        return price

    def __str__(self):
        return self.get_info()


if __name__ == "__main__":
    print(Information(TEST_PROPERTY_URL))
