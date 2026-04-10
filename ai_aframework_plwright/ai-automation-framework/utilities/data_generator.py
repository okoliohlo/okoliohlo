"""
Test Data Generator
Generates realistic test data using Faker
"""

from faker import Faker
from typing import Dict, List
import random
from utilities.logger import get_logger

logger = get_logger(__name__)
fake = Faker()


class TestDataGenerator:
    """Generates test data"""

    @staticmethod
    def generate_user(role: str = "standard") -> Dict:
        """
        Generate user data

        Args:
            role: User role (standard, admin, premium)

        Returns:
            User data dictionary
        """
        return {
            "username": fake.user_name(),
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=True, digits=True, upper_case=True),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "phone": fake.phone_number(),
            "role": role,
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
            "address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "zip_code": fake.zipcode(),
                "country": fake.country()
            }
        }

    @staticmethod
    def generate_product() -> Dict:
        """
        Generate product data

        Returns:
            Product data dictionary
        """
        return {
            "name": fake.catch_phrase(),
            "description": fake.text(max_nb_chars=200),
            "price": round(random.uniform(10, 1000), 2),
            "category": random.choice(["Electronics", "Clothing", "Books", "Home", "Sports"]),
            "stock": random.randint(0, 500),
            "sku": fake.ean13(),
            "brand": fake.company()
        }

    @staticmethod
    def generate_order(user_id: int = None, product_ids: List[int] = None) -> Dict:
        """
        Generate order data

        Args:
            user_id: User ID
            product_ids: List of product IDs

        Returns:
            Order data dictionary
        """
        return {
            "user_id": user_id or random.randint(1, 1000),
            "order_date": fake.date_time_this_year().isoformat(),
            "status": random.choice(["pending", "processing", "shipped", "delivered"]),
            "total_amount": round(random.uniform(50, 2000), 2),
            "shipping_address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "zip_code": fake.zipcode()
            },
            "items": [
                {
                    "product_id": pid,
                    "quantity": random.randint(1, 5),
                    "price": round(random.uniform(10, 500), 2)
                }
                for pid in (product_ids or [random.randint(1, 100) for _ in range(random.randint(1, 5))])
            ]
        }

    @staticmethod
    def generate_credit_card() -> Dict:
        """
        Generate credit card data

        Returns:
            Credit card data dictionary
        """
        return {
            "card_number": fake.credit_card_number(),
            "card_type": random.choice(["Visa", "MasterCard", "American Express"]),
            "expiry_month": str(random.randint(1, 12)).zfill(2),
            "expiry_year": str(random.randint(2024, 2030)),
            "cvv": str(random.randint(100, 999)),
            "cardholder_name": fake.name()
        }

    @staticmethod
    def generate_bulk_users(count: int) -> List[Dict]:
        """
        Generate multiple users

        Args:
            count: Number of users to generate

        Returns:
            List of user dictionaries
        """
        return [TestDataGenerator.generate_user() for _ in range(count)]

    @staticmethod
    def generate_bulk_products(count: int) -> List[Dict]:
        """
        Generate multiple products

        Args:
            count: Number of products to generate

        Returns:
            List of product dictionaries
        """
        return [TestDataGenerator.generate_product() for _ in range(count)]