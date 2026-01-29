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
            # Try new structure with class "price-text"
            price_elem = soup.find('span', class_='price-text')
            if not price_elem:
                # Fallback to old structure
                price_elem = soup.find('span', {'data-testid': 'price'})
            price = price_elem.text if price_elem else 'Price not available'
        except AttributeError:
            price = 'Price not available'

        try:
            address_elem = soup.find('h1')
            address = address_elem.text.strip() if address_elem else 'Address not available'
        except AttributeError:
            address = 'Address not available'

        try:
            # New structure: find all bed-bath-sqft-text__value elements
            value_spans = soup.find_all('span', {'data-testid': 'bed-bath-sqft-text__value'})
            desc_spans = soup.find_all('span', {'data-testid': 'bed-bath-sqft-text__description'})
            
            if len(value_spans) >= 3 and len(desc_spans) >= 3:
                beds = f"{value_spans[0].text} {desc_spans[0].text}"
                baths = f"{value_spans[1].text} {desc_spans[1].text}"
                sqft = f"{value_spans[2].text} {desc_spans[2].text}"
            else:
                # Fallback to old structure
                facts = soup.find_all('div', {'data-testid': 'bed-bath-sqft-fact-container'})
                beds = facts[0].text if len(facts) > 0 else 'N/A'
                baths = facts[1].text if len(facts) > 1 else 'N/A'
                sqft = facts[2].text if len(facts) > 2 else 'N/A'
        except (AttributeError, IndexError):
            beds, baths, sqft = 'N/A', 'N/A', 'N/A'

        try:
            # New structure: find at-a-glance section
            at_a_glance = soup.find('div', {'data-testid': 'at-a-glance'})
            year_built = 'N/A'
            land_area = 'N/A'
            
            if at_a_glance:
                # Find all text spans in the at-a-glance section
                text_spans = at_a_glance.find_all('span', class_=lambda c: c and 'llcOCk' in c)
                for span in text_spans:
                    text = span.text.strip()
                    if 'Built in' in text:
                        year_built = text
                    elif 'sqft' in text and ('acre' in text.lower() or any(char.isdigit() for char in text.split('sqft')[0])):
                        # Check if it's lot size (not the building sqft which is already captured)
                        # Lot size usually comes with "sqft" and is different from building sqft
                        if 'price' not in text.lower():
                            land_area = text
            
            # Fallback to old structure if new one didn't work
            if year_built == 'N/A' or land_area == 'N/A':
                others_container = soup.find('div', {'aria-label': "At a glance facts"})
                others = others_container.find_all('span') if others_container else []
                if year_built == 'N/A':
                    year_built = others[1].text if len(others) > 1 else 'N/A'
                if land_area == 'N/A':
                    land_area = others[2].text if len(others) > 2 else 'N/A'
        except (AttributeError, IndexError):
            year_built, land_area = 'N/A', 'N/A'

        try:
            # Try new structure with group-by-room photos
            gallery = soup.find('div', {'data-testid': 'group-by-room-list'})
            image_urls = []
            
            if gallery:
                # Find all picture/source elements for higher quality images
                pictures = gallery.find_all('picture')
                for picture in pictures:
                    # Try to get from source tag first (higher quality)
                    source = picture.find('source', {'type': 'image/jpeg'})
                    if source and source.get('srcset'):
                        # Get the highest resolution from srcset
                        srcset = source['srcset']
                        urls = [url.strip().split()[0] for url in srcset.split(',')]
                        if urls:
                            image_urls.append(urls[-1])  # Last one is usually highest res
                    else:
                        # Fallback to img tag
                        img = picture.find('img')
                        if img and img.get('src'):
                            image_urls.append(img['src'])
            else:
                # Fallback to old structure
                images_container = soup.find('div', {'data-testid': "hollywood-gallery-images-tile-list"})
                images = images_container.find_all('img') if images_container else []
                image_urls = [image['src'] for image in images if image.get('src')]
        except (AttributeError, TypeError):
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
