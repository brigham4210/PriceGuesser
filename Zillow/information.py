from bs4 import BeautifulSoup
import re

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

        try:
            # Price extraction
            price_elem = soup.find('span', class_='price-text')
            price = price_elem.text if price_elem else 'Price not available'
        except AttributeError:
            price = 'Price not available'

        try:
            # Address extraction
            address_elem = soup.find('h1')
            address = address_elem.text.strip() if address_elem else 'Address not available'
        except AttributeError:
            address = 'Address not available'

        try:
            # Beds, baths, sqft extraction
            value_spans = soup.find_all('span', {'data-testid': 'bed-bath-sqft-text__value'})
            desc_spans = soup.find_all('span', {'data-testid': 'bed-bath-sqft-text__description'})
            
            if len(value_spans) >= 3 and len(desc_spans) >= 3:
                beds = f"{value_spans[0].text} {desc_spans[0].text}"
                baths = f"{value_spans[1].text} {desc_spans[1].text}"
                sqft = f"{value_spans[2].text} {desc_spans[2].text}"
            else:
                beds, baths, sqft = 'N/A', 'N/A', 'N/A'
        except (AttributeError, IndexError):
            beds, baths, sqft = 'N/A', 'N/A', 'N/A'

        try:
            # Year built and land area extraction
            at_a_glance = soup.find('div', {'data-testid': 'at-a-glance'})
            year_built = 'N/A'
            land_area = 'N/A'
            
            if at_a_glance:
                text_spans = at_a_glance.find_all('span', class_=lambda c: c and 'llcOCk' in c)
                for span in text_spans:
                    text = span.text.strip()
                    if 'Built in' in text:
                        year_built = text
                    elif 'sqft' in text and 'price' not in text.lower():
                        land_area = text
        except (AttributeError, IndexError):
            year_built, land_area = 'N/A', 'N/A'

        try:
            # Image extraction - images are in JavaScript/JSON data, not HTML elements
            image_urls = []
            html_content = str(soup)
            
            # Try common Zillow image formats
            patterns = [
                r'https://photos\.zillowstatic\.com/fp/[a-f0-9]+-uncropped_scaled_within_1536_1152\.webp',
                r'https://photos\.zillowstatic\.com/fp/[a-f0-9]+-cc_ft_1536\.jpg',
            ]
            
            seen = set()
            for pattern in patterns:
                photo_urls = re.findall(pattern, html_content)
                for url in photo_urls:
                    if url not in seen:
                        seen.add(url)
                        image_urls.append(url)
                
                if len(image_urls) > 0:
                    break
            
            # Fallback: extract unique photo hashes and construct URLs
            if len(image_urls) == 0:
                all_urls = re.findall(r'https://photos\.zillowstatic\.com/fp/([a-f0-9]{32})-', html_content)
                seen_hashes = set()
                for photo_hash in all_urls:
                    if photo_hash not in seen_hashes:
                        seen_hashes.add(photo_hash)
                        image_urls.append(f"https://photos.zillowstatic.com/fp/{photo_hash}-cc_ft_1536.jpg")
            
            print(f"Found {len(image_urls)} property images")
        except Exception as e:
            print(f"Error extracting images: {e}")
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
