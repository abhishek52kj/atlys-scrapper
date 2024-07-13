# Atlys Scraper

Atlys Scraper is a Python-based web scraping tool developed using the FastAPI framework. It scrapes product information from the target website and stores it locally. The tool supports two versions of the API, each with different scraping techniques and capabilities.

## Features

- **Scrape Product Information:** Extract product name, price, and image from each page of the catalogue.
- **Limit Pages:** Option to limit the number of pages to scrape.
- **Proxy Support:** Option to use a proxy for scraping.
- **Data Storage:** Store scraped data in local JSON files (`scraped_products_v1.json` and `scraped_products_v2.json`).
- **Notification:** Prints scraping status and file details to the console.
- **Lazy-loaded Image Handling:** Properly handles lazy-loaded images.
- **Versioning:** Two versions of the API for different scraping techniques.

## Requirements

- Python 3.8+
- Redis (for caching purposes)

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/abhishek52kj/atlys_scraper.git
    cd atlys_scraper
    ```

2. Create and activate a virtual environment:
    ```sh
    python3 -m venv env
    source env/bin/activate
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Ensure Redis is running on your machine:
    ```sh
    redis-server
    ```

## Usage

1. Start the FastAPI server:
    ```sh
    uvicorn app.main:app --reload
    ```

2. Use the following endpoints to scrape data:

### Version 1 API

- **Endpoint:** `/v1/scrape`
- **Method:** `POST`
- **Request Body:**
    ```json
    {
      "page_limit": 5,
      "proxy": null
    }
    ```

- **Response:** JSON array of products scraped.

- **Example cURL Command:**
    ```sh
    curl -X POST "http://127.0.0.1:8000/v1/scrape" -H "Content-Type: application/json" -d '{"page_limit": 5, "proxy": null}'
    ```

### Version 2 API

- **Endpoint:** `/v2/scrape`
- **Method:** `POST`
- **Request Body:**
    ```json
    {
      "page_limit": 5,
      "proxy": null
    }
    ```

- **Response:** JSON array of products scraped.

- **Example cURL Command:**
    ```sh
    curl -X POST "http://127.0.0.1:8000/v2/scrape" -H "Content-Type: application/json" -d '{"page_limit": 5, "proxy": null}'
    ```

3. Check the console for the scraping status and file details.

## File Structure

```plaintext
atlys_scraper/
│
├── app/
│   ├── main.py
│   ├── scraper_v1.py
│   ├── scraper_v2.py
│   ├── storage.py
│
├── images/                   # Directory where images are saved ( will be created )
│
├── scraped_products_v1.json  # Scraped data for v1 ( will be created )
├── scraped_products_v2.json  # Scraped data for v2 ( will be created )
│
├── requirements.txt          # List of dependencies
├── README.md                 # Project documentation
