from bs4 import BeautifulSoup


class Properties:
    def __init__(self, url):
        self.url = url

    def property_urls(self):
        soup = BeautifulSoup(self.url, 'html.parser')
        property_list_section = soup.find('section', {'data-testid': 'property-list'})
        property_urls = []

        if property_list_section:
            property_cards = property_list_section.find_all('div', {'data-testid': 'card-content'})

            for card in property_cards:
                link_tag = card.find('a', href=True)
                if link_tag:
                    property_urls.append(link_tag['href'])

        return property_urls
