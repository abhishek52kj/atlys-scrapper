import json
from typing import List
from app.scraper_v1 import Product

def save_products(products: List[Product], file_path: str):
    try:
        existing_products = load_existing_products(file_path)
    except FileNotFoundError:
        existing_products = []

    for product in products:
        for existing_product in existing_products:
            if existing_product['product_title'] == product.product_title:
                existing_products.remove(existing_product)
                break
        existing_products.append(product.dict())

    with open(file_path, 'w') as f:
        json.dump(existing_products, f, indent=4)

def load_existing_products(file_path: str) -> List[dict]:
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data
