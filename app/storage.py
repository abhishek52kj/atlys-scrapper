import json
import os
from typing import List, Union
from app.scraper_v2 import Product
import sqlite3

class JSONStorage:
    def __init__(self, filename: str):
        self.filename = filename

    def load_existing_products(self) -> List[Product]:
        if not os.path.exists(self.filename):
            return []
        with open(self.filename, 'r') as f:
            data = json.load(f)
        return [Product(**item) for item in data]

    def save_products(self, products: List[Product]):
        existing_products = self.load_existing_products()
        updated_products = existing_products + products
        with open(self.filename, 'w') as f:
            json.dump([product.dict() for product in updated_products], f, indent=2)

    def notify_scraping_completed(self, product_count: int):
        print(f"Scraping completed. {product_count} products scraped.")
        print(f"Data saved to {self.filename}")


class SQLiteStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    product_title TEXT,
                    product_price REAL,
                    path_to_image TEXT
                )
            ''')

    def load_existing_products(self) -> List[Product]:
        cursor = self.conn.execute('SELECT product_title, product_price, path_to_image FROM products')
        rows = cursor.fetchall()
        return [Product(product_title=row[0], product_price=row[1], path_to_image=row[2]) for row in rows]

    def save_products(self, products: List[Product]):
        existing_products = self.load_existing_products()
        existing_titles = {p.product_title for p in existing_products}
        new_products = [p for p in products if p.product_title not in existing_titles]
        with self.conn:
            self.conn.executemany('INSERT INTO products (product_title, product_price, path_to_image) VALUES (?, ?, ?)',
                                  [(p.product_title, p.product_price, p.path_to_image) for p in new_products])

    def notify_scraping_completed(self, product_count: int):
        print(f"Scraping completed. {product_count} products scraped.")
        print(f"Data saved to {self.db_path}")


def get_storage(storage_type: str, path: str) -> Union[JSONStorage, SQLiteStorage]:
    if storage_type == "json":
        return JSONStorage(path)
    elif storage_type == "sqlite":
        return SQLiteStorage(path)
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")
