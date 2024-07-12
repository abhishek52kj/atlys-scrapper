from fastapi import FastAPI, Depends, HTTPException, status, Header
from typing import Optional
from pydantic import BaseModel
import app.scraper as scraper_module
import app.storage as storage_module

app = FastAPI()

# Authentication Dependency
def verify_token(authorization: str = Header(...)):
    if authorization != "Bearer static_token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

class ScrapingRequest(BaseModel):
    base_url: str
    page_limit: Optional[int] = 5
    proxy: Optional[str] = None

@app.post("/scrape", dependencies=[Depends(verify_token)])
async def scrape(scraping_request: ScrapingRequest):
    scraper = scraper_module.Scraper(
        base_url=scraping_request.base_url,
        page_limit=scraping_request.page_limit,
        proxy=scraping_request.proxy
    )
    products = await scraper.scrape()

    # Save the scraped products to a JSON file
    storage = storage_module.JSONStorage(file_path='scraped_products.json')
    storage.save_products(products)

    return products

@app.get("/")
def read_root():
    curl_command = (
        "curl -X POST http://127.0.0.1:8000/scrape "
        "-H \"Authorization: Bearer static_token\" "
        "-H \"Content-Type: application/json\" "
        "-d '{\"base_url\": \"https://dentalstall.com/shop/\", \"page_limit\": 5, \"proxy\": null}'"
    )
    return {
        "message": "Welcome to Atlys Scraper",
        "scrape API endpoint": curl_command,
    }