import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import aiofiles
import os
import redis
import logging

logger = logging.getLogger(__name__)

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
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error: {e.response.status_code} - {e.request.url}")
                except httpx.RequestError as e:
                    logger.error(f"Request error: {e}")
                except httpx.ReadTimeout as e:
                    logger.error(f"Read timeout: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                if i < retries - 1:
                    await asyncio.sleep(delay)
            raise Exception(f"Failed after {retries} retries")
        return wrapper
    return decorator

class Scraper:
    def __init__(self, base_url: str, page_limit: int = 5, proxy: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.page_limit = page_limit
        self.proxy = proxy
        self.client = httpx.AsyncClient(proxies=proxy, timeout=10.0, follow_redirects=True)
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)  # Updated Redis host

    @retry(retries=3, delay=2)
    async def fetch_page(self, page_number: int) -> str:
        url = f"{self.base_url}/page/{page_number}/"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.text

    @retry(retries=3, delay=2)
    async def fetch_product_details(self, url: str) -> Product:
        response = await self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('h1', class_='product_title entry-title').get_text(strip=True)
        price = soup.find('bdi').get_text(strip=True).replace('₹', '').replace(',', '')
        image_url = soup.find('img', class_='wp-post-image')['src']
        image_path = await self.download_image(image_url, title)
        return Product(
            product_title=title,
            product_price=float(price),
            path_to_image=image_path
        )

    @retry(retries=3, delay=2)
    async def download_image(self, url: str, title: str) -> str:
        response = await self.client.get(url)
        response.raise_for_status()
        image_extension = url.split('.')[-1]
        safe_title = title.replace(' ', '_').replace('/', '_').replace('\\', '_')
        file_path = f"images/{safe_title}.{image_extension}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(response.content)
        return file_path

    async def scrape(self) -> List[Product]:
        products = []
        for page_number in range(1, self.page_limit + 1):
            page_content = await self.fetch_page(page_number)
            soup = BeautifulSoup(page_content, 'html.parser')
            product_elements = soup.find_all('div', class_='product-inner')
            tasks = [self.fetch_product_details(e.find('a')['href']) for e in product_elements]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Product):
                    cached_price = self.redis_client.get(result.product_title)
                    if cached_price is not None:
                        cached_price = cached_price.decode('utf-8')
                    if cached_price is None or float(cached_price) != result.product_price:
                        self.redis_client.set(result.product_title, result.product_price)
                        products.append(result)
                else:
                    logger.error(f"Failed to fetch product details: {result}")
        await self.client.aclose()
        return products
