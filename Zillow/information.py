from bs4 import BeautifulSoup

from Zillow import SESSION, HEADERS, close_session
from Zillow.property import Property
from Zillow.url import Url


class Information:
    def __init__(self, url):
        # Coerce to string once to avoid repeated __str__ calls on objects like Property
        self.url = str(url)

    def get_info(self):
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

        images = soup.find('ul', {'aria-label': "media wall images"})
        print("Images section:")
        print(images)

        return f"""Address: {address}\nPrice: {price}\n{beds} {baths} {sqft} {land_area}\n{year_built} \n
        """

    def __str__(self):
        return self.get_info()


if __name__ == "__main__":
    # Get a concrete property URL string to avoid triggering Property.__str__ implicitly
    test_info = Information(
        Property(Url(state="in", bed_min=10, bed_max=None, bath_min=None, bath_max=None)).get_random_property_url())
    print(test_info)
