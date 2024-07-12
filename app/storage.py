import json
from typing import List
from app.scraper import Product

class JSONStorage:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_existing_products(self) -> List[Product]:
        try:
            with open(self.file_path, 'r') as f:
                data = f.read()
                if not data.strip():
                    return []
                return [Product(**product) for product in json.loads(data)]
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

    def save_products(self, products: List[Product]):
        existing_products = self.load_existing_products()
        existing_products_dict = {product.product_title: product for product in existing_products}
        
        updated_count = 0
        for product in products:
            if (product.product_title not in existing_products_dict or 
                existing_products_dict[product.product_title].product_price != product.product_price):
                existing_products_dict[product.product_title] = product
                updated_count += 1

        with open(self.file_path, 'w') as f:
            json.dump([product.dict() for product in existing_products_dict.values()], f, indent=4)
        
        self.notify(updated_count)

    def notify(self, product_count: int):
        print(f"Scraping completed. {product_count} products were processed.")
        print(f"Scraped data saved to: {self.file_path}")
