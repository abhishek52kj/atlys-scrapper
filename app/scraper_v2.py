import os
import httpx
import aiofiles
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import redis
import re

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
        self.image_dir = 'images'
        os.makedirs(self.image_dir, exist_ok=True)

    @retry(retries=3, delay=2)
    async def fetch_page(self, page_number: int) -> str:
        url = f"{self.base_url}/page/{page_number}/"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.text

    @retry(retries=3, delay=2)
    async def fetch_product_details(self, product_url: str) -> Product:
        response = await self.client.get(product_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        product_title = soup.find('h1', class_='product_title entry-title').get_text(strip=True)
        
        price_tag = soup.find('bdi')
        product_price = float(price_tag.get_text(strip=True).replace('₹', '').replace(',', ''))
        
        image_tag = soup.find('img', class_='wp-post-image')
        image_url = image_tag.get('src')
        
        image_path = await self.download_image(image_url, product_title)
        
        return Product(
            product_title=product_title,
            product_price=product_price,
            path_to_image=image_path
        )

    async def scrape(self) -> List[Product]:
        products = []
        for page_number in range(1, self.page_limit + 1):
            page_content = await self.fetch_page(page_number)
            soup = BeautifulSoup(page_content, 'html.parser')
            product_urls = self.extract_product_urls(soup)
            for url in product_urls:
                product = await self.fetch_product_details(url)
                cached_price = self.redis_client.get(product.product_title)
                if cached_price is not None:
                    cached_price = cached_price.decode('utf-8')
                if cached_price is None or float(cached_price) != product.product_price:
                    self.redis_client.set(product.product_title, product.product_price)
                    products.append(product)
        await self.client.aclose()
        return products

    def extract_product_urls(self, soup: BeautifulSoup) -> List[str]:
        product_elements = soup.find_all('div', class_='product-inner')
        product_urls = [element.find('a')['href'] for element in product_elements]
        return product_urls

    async def download_image(self, url: str, product_title: str) -> str:
        sanitized_title = re.sub(r'[^\w\s-]', '', product_title).replace(' ', '_')
        image_response = await self.client.get(url)
        image_response.raise_for_status()

        file_name = f"{sanitized_title}.jpg"
        file_path = os.path.join(self.image_dir, file_name)

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(image_response.content)

        return file_path
