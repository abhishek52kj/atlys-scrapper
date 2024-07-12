import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import aiofiles
import os
import redis

class Product(BaseModel):
    product_title: str
    product_price: float
    path_to_image: str

def retry(retries: int = 3, delay: int = 2):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for _ in range(retries):
                try:
                    return await func(*args, **kwargs)
                except (httpx.HTTPStatusError, httpx.RequestError, httpx.ReadTimeout) as e:
                    await asyncio.sleep(delay)
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
        self.image_dir = 'images'

        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

    @retry(retries=3, delay=2)
    async def fetch_page(self, page_number: int) -> str:
        url = f"{self.base_url}/page/{page_number}/"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.text

    async def scrape(self) -> List[Product]:
        products = []
        tasks = [self.scrape_page(page_number) for page_number in range(1, self.page_limit + 1)]
        pages_products = await asyncio.gather(*tasks)
        for page_products in pages_products:
            products.extend(page_products)
        await self.client.aclose()
        return products

    async def scrape_page(self, page_number: int) -> List[Product]:
        page_content = await self.fetch_page(page_number)
        soup = BeautifulSoup(page_content, 'html.parser')
        return await self.parse_products(soup)

    async def parse_products(self, soup: BeautifulSoup) -> List[Product]:
        product_elements = soup.find_all('div', class_='product-inner')
        products = []
        tasks = []

        for element in product_elements:
            link = element.find('a', href=True)
            if link:
                product_url = link['href']
                tasks.append(self.fetch_product_details(product_url))

        products = await asyncio.gather(*tasks)
        return products

    @retry(retries=3, delay=2)
    async def fetch_product_details(self, url: str) -> Product:
        response = await self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('h1', class_='product_title entry-title').get_text(strip=True)
        price = soup.find('span', class_='woocommerce-Price-amount').get_text(strip=True).replace('₹', '').replace(',', '')

        image_element = soup.find('img', class_='wp-post-image')
        if image_element and 'data-src' in image_element.attrs:
            image_url = image_element['data-src']
        else:
            image_url = image_element['src']

        image_path = await self.download_image(image_url, title)
        product = Product(product_title=title, product_price=float(price), path_to_image=image_path)

        cached_price = self.redis_client.get(product.product_title)
        if cached_price is not None:
            cached_price = cached_price.decode('utf-8')

        if cached_price is None or float(cached_price) != product.product_price:
            self.redis_client.set(product.product_title, product.product_price)

        return product

    @retry(retries=3, delay=2)
    async def download_image(self, url: str, title: str) -> str:
        response = await self.client.get(url)
        response.raise_for_status()
        file_name = f"{title.replace(' ', '_').replace('/', '_')}.jpg"
        file_path = os.path.join(self.image_dir, file_name)

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(response.content)

        return file_path
