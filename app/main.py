from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List, Optional
import app.scraper_v1 as scraper_v1
import app.scraper_v2 as scraper_v2
import app.storage as storage_module

app = FastAPI()

class ScrapeRequest(BaseModel):
    page_limit: Optional[int] = 5
    proxy: Optional[str] = None

@app.post("/v1/scrape")
async def scrape_v1(request: ScrapeRequest):
    scraper = scraper_v1.Scraper(
        base_url="https://dentalstall.com/shop/",
        page_limit=request.page_limit,
        proxy=request.proxy
    )
    products = await scraper.scrape()
    storage_module.save_products(products, 'scraped_products_v1.json')
    product_count = len(products)
    print(f"Scraping completed for v1. Products scraped: {product_count}, File: scraped_products_v1.json")
    return products

@app.post("/v2/scrape")
async def scrape_v2(request: ScrapeRequest):
    scraper = scraper_v2.Scraper(
        base_url="https://dentalstall.com/shop/",
        page_limit=request.page_limit,
        proxy=request.proxy
    )
    products = await scraper.scrape()
    storage_module.save_products(products, 'scraped_products_v2.json')
    product_count = len(products)
    print(f"Scraping completed for v2. Products scraped: {product_count}, File: scraped_products_v2.json")
    return products

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Atlys Scraper",
        "scrape API endpoint v1": "/v1/scrape",
        "scrape API endpoint v2": "/v2/scrape"
    }
