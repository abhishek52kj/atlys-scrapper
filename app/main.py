import logging
from fastapi import FastAPI
import app.scraper_v1 as scraper_v1
import app.scraper_v2 as scraper_v2
import app.storage as storage_module
from app.rate_limiter import RateLimiterMiddleware

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

app = FastAPI()

# Apply rate limiting middleware
app.add_middleware(RateLimiterMiddleware, max_requests=100, window_size=60)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Atlys Scraper",
        "scrape API endpoint v1": 'curl -X POST "http://127.0.0.1:8000/v1/scrape" -H "Content-Type: application/json" -d \'{"page_limit": 5, "proxy": null}\'',
        "scrape API endpoint v2": 'curl -X POST "http://127.0.0.1:8000/v2/scrape" -H "Content-Type: application/json" -d \'{"page_limit": 5, "proxy": null}\''
    }

@app.post("/v1/scrape")
async def scrape_v1():
    scraper = scraper_v1.Scraper(base_url="https://dentalstall.com/shop", page_limit=5)
    products = await scraper.scrape()
    storage = storage_module.JSONStorage("scraped_products_v1.json")
    storage.save_products(products)
    storage.notify_scraping_completed(len(products))
    return {"products": products}

@app.post("/v2/scrape")
async def scrape_v2():
    scraper = scraper_v2.Scraper(base_url="https://dentalstall.com/shop", page_limit=5)
    products = await scraper.scrape()
    storage = storage_module.JSONStorage("scraped_products_v2.json")
    storage.save_products(products)
    storage.notify_scraping_completed(len(products))
    return {"products": products}
