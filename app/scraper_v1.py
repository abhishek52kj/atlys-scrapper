import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import redis

class Product(BaseModel):
    product_title: str
    product_price: float
    path_to_image: str

def retry(retries: int = 3, delay: int = 2):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return await func(*args, **kwargs)
                except (httpx.HTTPStatusError, httpx.RequestError, httpx.ReadTimeout) as e:
                    if i < retries - 1:
                        await asyncio.sleep(delay)
                    else:
                        raise e
        return wrapper
    return decorator

class Scraper:
    def __init__(self, base_url: str, page_limit: int = 5, proxy: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.page_limit = page_limit
        self.proxy = proxy
        self.client = httpx.AsyncClient(proxies=proxy, timeout=10.0, follow_redirects=True)
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)

    @retry(retries=3, delay=2)
    async def fetch_page(self, page_number: int) -> str:
        url = f"{self.base_url}/page/{page_number}/"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.text

    async def scrape(self) -> List[Product]:
        products = []
        for page_number in range(1, self.page_limit + 1):
            page_content = await self.fetch_page(page_number)
            soup = BeautifulSoup(page_content, 'html.parser')
            products.extend(self.parse_products(soup))
        await self.client.aclose()
        return products

    def parse_products(self, soup: BeautifulSoup) -> List[Product]:
        product_elements = soup.find_all('div', class_='product-inner')
        products = []
        for element in product_elements:
            try:
                title = element.find('h2', class_='woo-loop-product__title').get_text(strip=True)
            except AttributeError:
                title = "No title found"

            try:
                price_ins = element.find('span', class_='price').find('ins')
                if price_ins:
                    price = price_ins.find('span', class_='woocommerce-Price-amount').get_text(strip=True).replace('₹', '').replace(',', '')
                else:
                    price_del = element.find('span', class_='price').find('del')
                    if price_del:
                        price = price_del.find('span', class_='woocommerce-Price-amount').get_text(strip=True).replace('₹', '').replace(',', '')
                    else:
                        price = element.find('span', class_='price').find('span', class_='woocommerce-Price-amount').get_text(strip=True).replace('₹', '').replace(',', '')
            except AttributeError:
                price = "0.0"

            try:
                img_tag = element.find('img', class_='attachment-woocommerce_thumbnail')
                image_url = img_tag.get('data-src') or img_tag.get('src')
                if image_url and image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url and not image_url.startswith('http'):
                    image_url = 'https://' + image_url.lstrip('/')
            except AttributeError:
                image_url = "No image found"

            product = Product(
                product_title=title,
                product_price=float(price),
                path_to_image=image_url
            )

            cached_price = self.redis_client.get(product.product_title)
            if cached_price is not None:
                cached_price = cached_price.decode('utf-8')

            if cached_price is None or float(cached_price) != product.product_price:
                self.redis_client.set(product.product_title, product.product_price)
                products.append(product)

        return products
