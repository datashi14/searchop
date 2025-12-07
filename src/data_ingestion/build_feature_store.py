"""Build feature store from catalog and clickstream data."""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

from src.utils.config import (
    CATALOG_FILE, EVENTS_FILE, FEATURE_STORE_FILE, PROCESSED_DATA_DIR
)
from src.utils.logging_utils import setup_logging

logger = setup_logging()


def compute_product_features(catalog_df: pd.DataFrame, events_df: pd.DataFrame) -> pd.DataFrame:
    """Compute product-level features."""
    logger.info("Computing product-level features...")
    
    # Aggregate events by product
    product_stats = events_df.groupby("product_id").agg({
        "event_id": "count",  # total views
        "clicked": "sum",     # total clicks
        "add_to_cart": "sum", # total add to cart
        "purchased": "sum",   # total purchases
    }).rename(columns={
        "event_id": "total_views",
        "clicked": "total_clicks",
        "add_to_cart": "total_add_to_cart",
        "purchased": "total_purchases",
    })
    
    # Compute rates
    product_stats["ctr"] = product_stats["total_clicks"] / (product_stats["total_views"] + 1)
    product_stats["atc_rate"] = product_stats["total_add_to_cart"] / (product_stats["total_views"] + 1)
    product_stats["purchase_rate"] = product_stats["total_purchases"] / (product_stats["total_views"] + 1)
    
    # Recency features (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_events = events_df[events_df["timestamp"] >= seven_days_ago]
    
    recent_stats = recent_events.groupby("product_id").agg({
        "event_id": "count",
        "purchased": "sum",
    }).rename(columns={
        "event_id": "recent_views_7d",
        "purchased": "recent_purchases_7d",
    })
    
    # Merge with catalog
    product_features = catalog_df.merge(
        product_stats,
        left_on="product_id",
        right_index=True,
        how="left"
    ).merge(
        recent_stats,
        left_on="product_id",
        right_index=True,
        how="left"
    )
    
    # Fill NaN values
    product_features["recent_views_7d"] = product_features["recent_views_7d"].fillna(0)
    product_features["recent_purchases_7d"] = product_features["recent_purchases_7d"].fillna(0)
    product_features["ctr"] = product_features["ctr"].fillna(0)
    product_features["atc_rate"] = product_features["atc_rate"].fillna(0)
    product_features["purchase_rate"] = product_features["purchase_rate"].fillna(0)
    
    # Popularity score (normalized total views)
    max_views = product_features["total_views"].max()
    if max_views > 0:
        product_features["popularity"] = product_features["total_views"] / max_views
    else:
        product_features["popularity"] = 0
    
    logger.info(f"Computed features for {len(product_features)} products")
    return product_features


def compute_query_product_features(
    events_df: pd.DataFrame,
    product_features: pd.DataFrame
) -> pd.DataFrame:
    """Compute query-product pair features."""
    logger.info("Computing query-product pair features...")
    
    # Aggregate by query and product
    query_product_stats = events_df.groupby(["query", "product_id"]).agg({
        "event_id": "count",
        "clicked": "sum",
        "purchased": "sum",
    }).rename(columns={
        "event_id": "query_product_views",
        "clicked": "query_product_clicks",
        "purchased": "query_product_purchases",
    }).reset_index()
    
    # Compute query-product specific rates
    query_product_stats["query_ctr"] = (
        query_product_stats["query_product_clicks"] / 
        (query_product_stats["query_product_views"] + 1)
    )
    query_product_stats["query_purchase_rate"] = (
        query_product_stats["query_product_purchases"] / 
        (query_product_stats["query_product_views"] + 1)
    )
    
    # Merge with product features
    query_product_features = query_product_stats.merge(
        product_features,
        on="product_id",
        how="left"
    )
    
    logger.info(f"Computed features for {len(query_product_features)} query-product pairs")
    return query_product_features


def compute_tfidf_similarity(query: str, title: str) -> float:
    """Simple TF-IDF-like similarity between query and product title."""
    query_words = set(query.lower().split())
    title_words = set(title.lower().split())
    
    if not query_words or not title_words:
        return 0.0
    
    # Jaccard similarity (simple approximation)
    intersection = len(query_words & title_words)
    union = len(query_words | title_words)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def build_feature_store() -> pd.DataFrame:
    """Build complete feature store."""
    logger.info("Loading raw data...")
    
    # Load data
    catalog_df = pd.read_csv(CATALOG_FILE)
    events_df = pd.read_csv(EVENTS_FILE)
    
    # Convert timestamp
    events_df["timestamp"] = pd.to_datetime(events_df["timestamp"])
    
    logger.info(f"Loaded {len(catalog_df)} products and {len(events_df)} events")
    
    # Compute product features
    product_features = compute_product_features(catalog_df, events_df)
    
    # Compute query-product features
    query_product_features = compute_query_product_features(events_df, product_features)
    
    # Add TF-IDF similarity feature
    logger.info("Computing TF-IDF similarity features...")
    query_product_features["tfidf_similarity"] = query_product_features.apply(
        lambda row: compute_tfidf_similarity(row["query"], row["title"]),
        axis=1
    )
    
    # Select final feature columns
    feature_columns = [
        # Identifiers
        "query",
        "product_id",
        "user_id",  # Will be None for most, but kept for structure
        
        # Product features
        "title",
        "description",
        "category",
        "price",
        "brand",
        "rating",
        "tags",
        
        # Aggregated product features
        "total_views",
        "total_clicks",
        "total_add_to_cart",
        "total_purchases",
        "ctr",
        "atc_rate",
        "purchase_rate",
        "recent_views_7d",
        "recent_purchases_7d",
        "popularity",
        
        # Query-product features
        "query_product_views",
        "query_product_clicks",
        "query_product_purchases",
        "query_ctr",
        "query_purchase_rate",
        "tfidf_similarity",
    ]
    
    # Ensure all columns exist
    available_columns = [col for col in feature_columns if col in query_product_features.columns]
    feature_store = query_product_features[available_columns].copy()
    
    logger.info(f"Feature store shape: {feature_store.shape}")
    logger.info(f"Feature columns: {len(feature_store.columns)}")
    
    return feature_store


def main():
    """Build feature store and save to parquet."""
    logger.info("Starting feature store construction...")
    
    feature_store = build_feature_store()
    
    # Save to parquet
    feature_store.to_parquet(FEATURE_STORE_FILE, index=False, engine="pyarrow")
    logger.info(f"Saved feature store to {FEATURE_STORE_FILE}")
    
    # Also save a sample for inspection
    sample_file = PROCESSED_DATA_DIR / "feature_store_sample.csv"
    feature_store.head(100).to_csv(sample_file, index=False)
    logger.info(f"Saved sample to {sample_file}")
    
    # Print summary statistics
    logger.info("\nFeature Store Summary:")
    logger.info(f"Total query-product pairs: {len(feature_store)}")
    logger.info(f"Unique queries: {feature_store['query'].nunique()}")
    logger.info(f"Unique products: {feature_store['product_id'].nunique()}")
    logger.info(f"\nFeature ranges:")
    logger.info(f"  CTR: {feature_store['ctr'].min():.4f} - {feature_store['ctr'].max():.4f}")
    logger.info(f"  Purchase rate: {feature_store['purchase_rate'].min():.4f} - {feature_store['purchase_rate'].max():.4f}")
    logger.info(f"  Query CTR: {feature_store['query_ctr'].min():.4f} - {feature_store['query_ctr'].max():.4f}")
    logger.info(f"  TF-IDF similarity: {feature_store['tfidf_similarity'].min():.4f} - {feature_store['tfidf_similarity'].max():.4f}")
    
    logger.info("Feature store construction complete!")


if __name__ == "__main__":
    main()

