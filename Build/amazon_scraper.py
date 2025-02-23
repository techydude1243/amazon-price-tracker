import requests
from bs4 import BeautifulSoup
import logging
import re

logger = logging.getLogger(__name__)

def get_product_details(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    
    for attempt in range(3):  # Retry mechanism
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.content, "lxml")

        # Check for CAPTCHA
        if "Enter the characters you see below" in soup.text:
            logger.error("Encountered CAPTCHA, retrying...")
            continue

        name_element = soup.find(id="productTitle")
        price_element = soup.find("span", {"class": "a-offscreen"})
        
        if not name_element or not price_element:
            logger.error(f"Could not find product name or price for URL: {url}")
            logger.debug(f"HTML Content: {soup.prettify()}")
            raise ValueError("Could not find product name or price on the page. The page structure might have changed.")

        name = name_element.get_text().strip()
        price = price_element.get_text().strip()
        
        # Remove any currency symbols and commas, then convert to float
        price = re.sub(r'[^\d.]', '', price)
        price = float(price)
        
        logger.debug(f"Product details - Name: {name}, Price: {price}")
        return {"name": name, "price": price}

    raise ValueError("Failed to retrieve product details after multiple attempts due to CAPTCHA.")