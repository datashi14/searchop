"""Generate realistic demo e-commerce dataset with noise and imperfections."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import random
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import RAW_DATA_DIR, CATALOG_FILE, EVENTS_FILE
from src.utils.logging_utils import setup_logging

logger = setup_logging()

# More realistic product categories
CATEGORIES = [
    "electronics", "clothing", "home_garden", "sports_outdoors",
    "books", "toys_games", "beauty_personal_care", "automotive",
    "food_beverages", "health_wellness"
]

# Realistic brands by category
BRANDS = {
    "electronics": ["Sony", "Samsung", "Apple", "LG", "Panasonic", "Generic"],
    "clothing": ["Nike", "Adidas", "Levi's", "Gap", "H&M", "Generic"],
    "home_garden": ["IKEA", "Home Depot", "Target", "Generic"],
    "sports_outdoors": ["Nike", "Adidas", "Under Armour", "Generic"],
    "books": ["Penguin", "Random House", "HarperCollins", "Generic"],
    "toys_games": ["LEGO", "Hasbro", "Mattel", "Generic"],
    "beauty_personal_care": ["L'Oreal", "Maybelline", "MAC", "Generic"],
    "automotive": ["3M", "Bosch", "Michelin", "Generic"],
    "food_beverages": ["Generic", "Brand A", "Brand B"],
    "health_wellness": ["Generic", "Brand X", "Brand Y"],
}

# Realistic search queries (with typos and variations)
SEARCH_QUERIES = [
    "laptop", "running shoes", "headphones", "smartphone", "jeans",
    "coffee maker", "yoga mat", "backpack", "watch", "camera",
    "tablet", "sneakers", "jacket", "dress", "shirt", "boots",
    "sunglasses", "basketball", "bike", "lamp", "chair", "novel",
    "action figure", "lipstick", "tire", "battery", "phone case",
    "wireless earbuds", "gaming mouse", "keyboard", "monitor",
    "bluetooth speaker", "fitness tracker", "water bottle", "umbrella"
]


def generate_realistic_catalog(n_products: int = 2000, seed: int = 42) -> pd.DataFrame:
    """Generate realistic product catalog with noise."""
    logger.info(f"Generating realistic catalog with {n_products} products...")
    np.random.seed(seed)
    random.seed(seed)
    
    products = []
    
    for product_id in range(1, n_products + 1):
        category = np.random.choice(CATEGORIES)
        brand = np.random.choice(BRANDS.get(category, ["Generic"]))
        
        # More realistic title generation
        if category == "electronics":
            titles = ["Wireless Headphones", "Smart Watch", "Bluetooth Speaker", 
                     "USB-C Cable", "Phone Case", "Screen Protector"]
        elif category == "clothing":
            titles = ["T-Shirt", "Jeans", "Hoodie", "Jacket", "Sneakers", "Shorts"]
        elif category == "home_garden":
            titles = ["Desk Lamp", "Coffee Table", "Throw Pillow", "Plant Pot", "Wall Clock"]
        else:
            titles = ["Product", "Item", "Good"]
        
        title_base = np.random.choice(titles)
        title = f"{brand} {title_base}"
        if np.random.random() < 0.3:  # 30% have model numbers
            title += f" {np.random.randint(100, 999)}"
        
        # Realistic price distribution (with outliers)
        if category in ["electronics"]:
            base_price = np.random.lognormal(mean=4.5, sigma=0.9)
        elif category in ["clothing", "sports_outdoors"]:
            base_price = np.random.lognormal(mean=3.8, sigma=0.7)
        else:
            base_price = np.random.lognormal(mean=3.2, sigma=0.6)
        
        # Add some noise
        price = base_price * np.random.uniform(0.8, 1.2)
        price = round(price, 2)
        
        # Rating with realistic distribution (most products 3.5-4.5)
        rating = np.random.beta(a=7, b=3) * 2 + 3  # Skewed towards 3-5
        rating = round(rating, 1)
        
        # Stock status (some out of stock)
        stock = np.random.choice([0, 1, 1, 1, 1], p=[0.1, 0.225, 0.225, 0.225, 0.225])
        
        # Popularity score (some products more popular)
        popularity_score = np.random.exponential(scale=0.3)
        popularity_score = min(popularity_score, 1.0)
        
        # Tags
        all_tags = ["bestseller", "new", "sale", "premium", "eco-friendly", 
                   "limited", "trending", "classic", "modern", "popular"]
        n_tags = np.random.poisson(lam=2.5)
        n_tags = max(1, min(n_tags, 5))
        tags = ",".join(np.random.choice(all_tags, size=n_tags, replace=False))
        
        products.append({
            "product_id": product_id,
            "title": title,
            "description": f"High-quality {title_base.lower()} from {brand}.",
            "category": category,
            "price": price,
            "brand": brand,
            "rating": rating,
            "stock": stock,
            "popularity_score": popularity_score,
            "tags": tags,
        })
    
    catalog_df = pd.DataFrame(products)
    logger.info(f"Generated {len(catalog_df)} products across {catalog_df['category'].nunique()} categories")
    return catalog_df


def generate_realistic_events(
    catalog_df: pd.DataFrame,
    n_users: int = 1000,
    n_events: int = 100000,
    days_back: int = 60,
    seed: int = 42
) -> pd.DataFrame:
    """Generate realistic clickstream events with noise."""
    logger.info(f"Generating {n_events} realistic events for {n_users} users...")
    np.random.seed(seed)
    random.seed(seed)
    
    product_ids = catalog_df["product_id"].tolist()
    events = []
    
    # User segments (some users more active, some prefer certain categories)
    user_segments = {}
    for user_id in range(1, n_users + 1):
        segment = np.random.choice(["high_activity", "medium_activity", "low_activity"], 
                                  p=[0.2, 0.5, 0.3])
        preferred_categories = np.random.choice(
            CATEGORIES, 
            size=np.random.randint(0, 3), 
            replace=False
        ).tolist()
        user_segments[f"u-{user_id}"] = {
            "segment": segment,
            "preferred_categories": preferred_categories
        }
    
    start_date = datetime.now() - timedelta(days=days_back)
    
    for event_id in range(1, n_events + 1):
        user_id = f"u-{np.random.randint(1, n_users + 1)}"
        user_info = user_segments[user_id]
        
        # Activity level affects event frequency
        if user_info["segment"] == "high_activity":
            activity_multiplier = 1.5
        elif user_info["segment"] == "low_activity":
            activity_multiplier = 0.5
        else:
            activity_multiplier = 1.0
        
        # Skip some events for low activity users
        if np.random.random() > activity_multiplier * 0.7:
            continue
        
        product_id = np.random.choice(product_ids)
        product = catalog_df[catalog_df["product_id"] == product_id].iloc[0]
        
        # Query generation (more realistic with typos and variations)
        if np.random.random() < 0.6:  # 60% category-related
            if product["category"] in user_info["preferred_categories"]:
                # User searches for preferred category
                category_queries = {
                    "electronics": ["laptop", "phone", "headphones", "tablet"],
                    "clothing": ["shoes", "jeans", "shirt", "jacket"],
                    "sports_outdoors": ["running shoes", "yoga mat", "bike"],
                }
                queries = category_queries.get(product["category"], SEARCH_QUERIES[:5])
                query = np.random.choice(queries)
            else:
                query = np.random.choice(SEARCH_QUERIES)
        else:
            # Random query (might not match product)
            query = np.random.choice(SEARCH_QUERIES)
        
        # Add query variations (typos, plurals)
        if np.random.random() < 0.1:  # 10% have variations
            if query.endswith("s"):
                query = query[:-1]  # Remove plural
            elif np.random.random() < 0.5:
                query = query + "s"  # Add plural
        
        # Timestamp (more events recently, some old)
        days_ago = np.random.exponential(scale=days_back / 4)
        days_ago = min(days_ago, days_back)
        timestamp = start_date + timedelta(
            days=days_ago,
            hours=np.random.randint(0, 24),
            minutes=np.random.randint(0, 60)
        )
        
        # Event type with realistic funnel (with noise)
        rand = np.random.random()
        
        # Base probabilities
        if rand < 0.65:  # 65% impressions/views
            event_type = "view"
            clicked = False
            add_to_cart = False
            purchased = False
        elif rand < 0.88:  # 23% clicks
            # Click probability depends on relevance
            relevance = compute_relevance(query, product)
            click_prob = 0.3 * relevance + 0.1  # Base 10%, up to 40% for high relevance
            
            # User preference affects click
            if product["category"] in user_info["preferred_categories"]:
                click_prob *= 1.3
            
            clicked = np.random.random() < click_prob
            event_type = "click" if clicked else "view"
            add_to_cart = False
            purchased = False
        elif rand < 0.96:  # 8% add to cart
            event_type = "add_to_cart"
            clicked = True
            # ATC probability lower for expensive items
            atc_prob = 0.4 if product["price"] < 100 else 0.2
            add_to_cart = np.random.random() < atc_prob
            purchased = False
        else:  # 4% purchases
            event_type = "purchase"
            clicked = True
            add_to_cart = True
            # Purchase probability even lower
            purchase_prob = 0.3 if product["price"] < 50 else 0.15
            purchased = np.random.random() < purchase_prob
        
        # Add noise: some events don't follow funnel
        if np.random.random() < 0.05:  # 5% noise
            if event_type == "purchase" and not add_to_cart:
                add_to_cart = True  # Fix funnel violation
            if event_type in ["add_to_cart", "purchase"] and not clicked:
                clicked = True
        
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


def compute_relevance(query: str, product: dict) -> float:
    """Compute simple relevance score between query and product."""
    query_words = set(query.lower().split())
    title_words = set(product["title"].lower().split())
    category = product["category"].lower()
    
    # Exact match
    if query.lower() in product["title"].lower():
        return 1.0
    
    # Word overlap
    if query_words & title_words:
        return 0.7
    
    # Category match
    if any(qw in category for qw in query_words):
        return 0.4
    
    # Brand match
    if any(qw in product["brand"].lower() for qw in query_words):
        return 0.5
    
    # Low relevance
    return 0.1


def main():
    """Generate realistic demo data."""
    logger.info("Generating realistic demo dataset...")
    
    # Generate catalog
    catalog_df = generate_realistic_catalog(n_products=2000)
    catalog_df.to_csv(CATALOG_FILE, index=False)
    logger.info(f"Saved catalog to {CATALOG_FILE}")
    
    # Generate events
    events_df = generate_realistic_events(
        catalog_df=catalog_df,
        n_users=1000,
        n_events=100000,
        days_back=60
    )
    events_df.to_csv(EVENTS_FILE, index=False)
    logger.info(f"Saved events to {EVENTS_FILE}")
    
    logger.info("Demo data generation complete!")
    logger.info(f"Catalog: {len(catalog_df)} products")
    logger.info(f"Events: {len(events_df)} events")
    logger.info(f"Event funnel: {events_df['event_type'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()

