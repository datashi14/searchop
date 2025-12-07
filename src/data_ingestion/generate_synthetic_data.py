"""Generate synthetic e-commerce catalog and clickstream data.

This is the original simple generator. For more realistic demo data,
use scripts/generate_demo_data.py instead.
"""
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.utils.config import CATALOG_FILE, EVENTS_FILE
from src.utils.logging_utils import setup_logging

logger = setup_logging()

# Product categories and brands
CATEGORIES = [
    "footwear", "apparel", "electronics", "accessories", "sports",
    "home", "books", "toys", "beauty", "automotive"
]

BRANDS = {
    "footwear": ["Nike", "Adidas", "Puma", "Reebok", "New Balance"],
    "apparel": ["Zara", "H&M", "Uniqlo", "Levi's", "Gap"],
    "electronics": ["Apple", "Samsung", "Sony", "LG", "Canon"],
    "accessories": ["Fossil", "Michael Kors", "Coach", "Kate Spade"],
    "sports": ["Under Armour", "Nike", "Adidas", "Wilson", "Spalding"],
    "home": ["IKEA", "Target", "Home Depot", "Wayfair"],
    "books": ["Penguin", "HarperCollins", "Random House"],
    "toys": ["LEGO", "Hasbro", "Mattel", "Fisher-Price"],
    "beauty": ["L'Oreal", "Maybelline", "MAC", "Sephora"],
    "automotive": ["3M", "Bosch", "Michelin", "Goodyear"],
}

# Common product titles by category
PRODUCT_TITLES = {
    "footwear": ["Running Shoes", "Sneakers", "Boots", "Sandals", "Slippers"],
    "apparel": ["T-Shirt", "Jeans", "Hoodie", "Jacket", "Dress"],
    "electronics": ["Smartphone", "Laptop", "Headphones", "Camera", "Tablet"],
    "accessories": ["Watch", "Bag", "Wallet", "Sunglasses", "Belt"],
    "sports": ["Basketball", "Tennis Racket", "Yoga Mat", "Dumbbells", "Bike"],
    "home": ["Lamp", "Chair", "Table", "Rug", "Curtains"],
    "books": ["Novel", "Biography", "Cookbook", "Textbook", "Comic"],
    "toys": ["Action Figure", "Board Game", "Puzzle", "Doll", "RC Car"],
    "beauty": ["Lipstick", "Foundation", "Mascara", "Perfume", "Moisturizer"],
    "automotive": ["Tire", "Battery", "Oil Filter", "Brake Pad", "Air Freshener"],
}

# Common search queries
SEARCH_QUERIES = [
    "running shoes", "black hoodie", "laptop", "wireless headphones",
    "smartphone", "jeans", "watch", "backpack", "camera", "tablet",
    "sneakers", "jacket", "dress", "shirt", "boots", "sunglasses",
    "basketball", "yoga mat", "bike", "lamp", "chair", "novel",
    "action figure", "lipstick", "tire", "battery"
]


def generate_catalog(n_products: int = 1000, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic product catalog."""
    logger.info(f"Generating catalog with {n_products} products...")
    np.random.seed(seed)
    random.seed(seed)
    
    products = []
    
    for product_id in range(1, n_products + 1):
        category = np.random.choice(CATEGORIES)
        brand = np.random.choice(BRANDS.get(category, ["Generic"]))
        title_base = np.random.choice(PRODUCT_TITLES.get(category, ["Product"]))
        title = f"{brand} {title_base} {product_id % 100}"
        
        # Generate realistic descriptions
        description = (
            f"High-quality {title_base.lower()} from {brand}. "
            f"Perfect for everyday use. Features premium materials and excellent craftsmanship."
        )
        
        # Price distribution (some products more expensive)
        if category in ["electronics", "apparel"]:
            price = np.random.lognormal(mean=4.0, sigma=0.8)
        else:
            price = np.random.lognormal(mean=3.0, sigma=0.7)
        price = round(price, 2)
        
        # Rating (most products have good ratings)
        rating = np.random.beta(a=8, b=2) * 5  # Skewed towards higher ratings
        rating = round(rating, 1)
        
        # Tags (2-4 tags per product)
        n_tags = np.random.randint(2, 5)
        all_tags = ["popular", "new", "sale", "premium", "eco-friendly", 
                    "bestseller", "limited", "trending", "classic", "modern"]
        tags = ",".join(np.random.choice(all_tags, size=n_tags, replace=False))
        
        products.append({
            "product_id": product_id,
            "title": title,
            "description": description,
            "category": category,
            "price": price,
            "brand": brand,
            "rating": rating,
            "tags": tags,
        })
    
    catalog_df = pd.DataFrame(products)
    logger.info(f"Generated {len(catalog_df)} products across {catalog_df['category'].nunique()} categories")
    return catalog_df


def generate_clickstream_events(
    catalog_df: pd.DataFrame,
    n_users: int = 500,
    n_events: int = 50000,
    days_back: int = 30,
    seed: int = 42
) -> pd.DataFrame:
    """Generate synthetic clickstream events."""
    logger.info(f"Generating {n_events} clickstream events for {n_users} users...")
    np.random.seed(seed)
    random.seed(seed)
    
    product_ids = catalog_df["product_id"].tolist()
    events = []
    
    # Create user-product affinity (some users prefer certain categories)
    user_preferences = {}
    for user_id in range(1, n_users + 1):
        preferred_categories = np.random.choice(
            CATEGORIES, 
            size=np.random.randint(1, 4), 
            replace=False
        )
        user_preferences[f"u-{user_id}"] = preferred_categories.tolist()
    
    start_date = datetime.now() - timedelta(days=days_back)
    
    for event_id in range(1, n_events + 1):
        user_id = f"u-{np.random.randint(1, n_users + 1)}"
        product_id = np.random.choice(product_ids)
        
        # Get product category
        product = catalog_df[catalog_df["product_id"] == product_id].iloc[0]
        product_category = product["category"]
        
        # User preference affects click probability
        user_likes_category = product_category in user_preferences.get(user_id, [])
        
        # Generate query (sometimes related to product, sometimes random)
        if np.random.random() < 0.7:  # 70% of queries are product-related
            # Query related to product category or title
            if np.random.random() < 0.5:
                query = np.random.choice(SEARCH_QUERIES)
            else:
                # Query based on product attributes
                query_parts = [product["title"].split()[0]]  # Brand or first word
                if np.random.random() < 0.5:
                    query_parts.append(product["category"])
                query = " ".join(query_parts)
        else:
            query = np.random.choice(SEARCH_QUERIES)
        
        # Generate timestamp (distributed over last N days)
        days_ago = np.random.exponential(scale=days_back / 3)
        days_ago = min(days_ago, days_back)
        timestamp = start_date + timedelta(days=days_ago, hours=np.random.randint(0, 24))
        
        # Event type probabilities (funnel: view > click > add_to_cart > purchase)
        rand = np.random.random()
        
        if rand < 0.6:  # 60% views
            event_type = "view"
            clicked = False
            add_to_cart = False
            purchased = False
        elif rand < 0.85:  # 25% clicks
            event_type = "click"
            clicked = True
            # Higher click probability if user likes category
            if user_likes_category:
                clicked = np.random.random() < 0.8
            add_to_cart = False
            purchased = False
        elif rand < 0.95:  # 10% add to cart
            event_type = "add_to_cart"
            clicked = True
            add_to_cart = True
            purchased = False
        else:  # 5% purchases
            event_type = "purchase"
            clicked = True
            add_to_cart = True
            purchased = True
        
        # Price affects purchase probability
        if event_type in ["add_to_cart", "purchase"]:
            if product["price"] > 200:
                # Lower probability for expensive items
                if np.random.random() > 0.3:
                    event_type = "click"
                    add_to_cart = False
                    purchased = False
        
        events.append({
            "event_id": event_id,
            "user_id": user_id,
            "product_id": product_id,
            "query": query.lower(),
            "event_type": event_type,
            "clicked": clicked,
            "add_to_cart": add_to_cart,
            "purchased": purchased,
            "timestamp": timestamp,
        })
    
    events_df = pd.DataFrame(events)
    logger.info(f"Generated {len(events_df)} events")
    logger.info(f"Event type distribution:\n{events_df['event_type'].value_counts()}")
    
    return events_df


def main():
    """Generate synthetic data and save to files."""
    logger.info("Starting synthetic data generation...")
    
    # Generate catalog
    catalog_df = generate_catalog(n_products=1000)
    catalog_df.to_csv(CATALOG_FILE, index=False)
    logger.info(f"Saved catalog to {CATALOG_FILE}")
    
    # Generate clickstream events
    events_df = generate_clickstream_events(
        catalog_df=catalog_df,
        n_users=500,
        n_events=50000,
        days_back=30
    )
    events_df.to_csv(EVENTS_FILE, index=False)
    logger.info(f"Saved events to {EVENTS_FILE}")
    
    logger.info("Data generation complete!")
    logger.info(f"Catalog: {len(catalog_df)} products")
    logger.info(f"Events: {len(events_df)} events")


if __name__ == "__main__":
    main()

