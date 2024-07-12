# Atlys Scraper

Welcome to Atlys Scraper, a Python FastAPI project that automates the scraping of product information from the specified target website.

## Features

- Scrapes product name, price, and image(link) from each page of the catalog.
- Supports optional settings for limiting the number of pages to scrape and using a proxy.
- Stores scraped information in a JSON file.
- Notifies the number of products processed.
- Simple authentication using a static token.
- Retry mechanism for failed requests.
- Caching of scraping results using Redis to avoid redundant updates.

## Requirements

- Python 3.8+
- Redis

## Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/atlys_scraper.git
    cd atlys_scraper
    ```

2. **Create and activate a virtual environment**:

    On macOS/Linux:
    ```bash
    python3 -m venv env
    source env/bin/activate
    ```

    On Windows:
    ```bash
    python -m venv env
    .\env\Scripts\activate
    ```

3. **Install the dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Ensure Redis is running**:

    You can start Redis with the following command if you have it installed locally:
    ```bash
    redis-server
    ```

    If you don't have Redis installed, you can follow the instructions [here](https://redis.io/download) to install it.

## Usage

1. **Run the FastAPI server**:

    ```bash
    uvicorn app.main:app --reload
    ```

2. **API Endpoints**:

    - **Root Endpoint**:
        ```http
        GET http://127.0.0.1:8000/
        ```
        - Response:
            ```json
            {
                "message": "Welcome to Atlys Scraper",
                "scrape API endpoint": "curl -X POST http://127.0.0.1:8000/scrape -H \"Authorization: Bearer static_token\" -H \"Content-Type: application/json\" -d '{\"base_url\": \"https://dentalstall.com/shop/\", \"page_limit\": 5, \"proxy\": null}'"
            }
            ```

    - **Scrape Endpoint**:
        ```http
        POST http://127.0.0.1:8000/scrape
        ```
        - Headers:
            ```json
            {
                "Authorization": "Bearer static_token",
                "Content-Type": "application/json"
            }
            ```
        - Body:
            ```json
            {
                "base_url": "https://dentalstall.com/shop/",
                "page_limit": 5,
                "proxy": null
            }
            ```
        - Response:
            ```json
            [
                {
                    "product_title": "Product Name",
                    "product_price": 100.0,
                    "path_to_image": "https://example.com/image.jpg"
                },
                ...
            ]
            ```

## Project Structure

```plaintext
atlys_scraper/
├── app/
│   ├── main.py
│   ├── scraper.py
│   └── storage.py
├── env/
├── .gitignore
├── README.md
└── requirements.txt
