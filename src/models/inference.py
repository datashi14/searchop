"""Model inference utilities."""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Optional
import sys

from src.utils.config import (
    FEATURE_STORE_FILE, MODELS_DIR, CURRENT_MODEL_VERSION_FILE
)
from src.utils.logging_utils import setup_logging

logger = setup_logging()


def load_model(version: Optional[str] = None):
    """Load model from registry."""
    if version is None:
        # Load current model version
        if CURRENT_MODEL_VERSION_FILE.exists():
            version = CURRENT_MODEL_VERSION_FILE.read_text().strip()
        else:
            # Find latest version
            model_files = sorted(MODELS_DIR.glob("model_v*.pkl"))
            if not model_files:
                raise FileNotFoundError("No model files found")
            version = model_files[-1].stem.replace("model_", "")
    
    model_path = MODELS_DIR / f"model_{version}.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    logger.info(f"Loading model: {model_path}")
    with open(model_path, "rb") as f:
        model_data = pickle.load(f)
    
    return model_data["model"], model_data["feature_cols"], version


def load_feature_store():
    """Load feature store."""
    if not FEATURE_STORE_FILE.exists():
        raise FileNotFoundError(f"Feature store not found: {FEATURE_STORE_FILE}")
    
    return pd.read_parquet(FEATURE_STORE_FILE)


def compute_tfidf_similarity(query: str, title: str) -> float:
    """Compute TF-IDF similarity between query and title."""
    query_words = set(query.lower().split())
    title_words = set(title.lower().split())
    
    if not query_words or not title_words:
        return 0.0
    
    intersection = len(query_words & title_words)
    union = len(query_words | title_words)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def prepare_features_for_ranking(
    query: str,
    products: List[Dict],
    feature_store: pd.DataFrame
) -> pd.DataFrame:
    """Prepare features for ranking given query and products."""
    product_ids = [p["id"] for p in products]
    
    # Get features for these products
    product_features = feature_store[
        (feature_store["product_id"].isin(product_ids))
    ].copy()
    
    # For products not in feature store, create default features
    found_ids = set(product_features["product_id"].unique())
    missing_ids = set(product_ids) - found_ids
    
    if missing_ids:
        logger.warning(f"Products not in feature store: {missing_ids}")
        # Create default rows for missing products
        default_rows = []
        for product_id in missing_ids:
            product = next((p for p in products if p["id"] == product_id), {})
            default_rows.append({
                "product_id": product_id,
                "query": query,
                "ctr": 0.0,
                "atc_rate": 0.0,
                "purchase_rate": 0.0,
                "recent_views_7d": 0.0,
                "recent_purchases_7d": 0.0,
                "popularity": 0.0,
                "query_ctr": 0.0,
                "query_purchase_rate": 0.0,
                "tfidf_similarity": compute_tfidf_similarity(query, product.get("title", "")),
                "price": product.get("price", 0.0),
                "rating": product.get("rating", 0.0),
            })
        
        if default_rows:
            default_df = pd.DataFrame(default_rows)
            product_features = pd.concat([product_features, default_df], ignore_index=True)
    
    # Filter to query-specific features if available
    query_specific = product_features[product_features["query"] == query.lower()]
    if len(query_specific) > 0:
        product_features = query_specific
    
    # Ensure we have one row per product
    product_features = product_features.groupby("product_id").first().reset_index()
    
    return product_features


def rank_products(
    query: str,
    products: List[Dict],
    model=None,
    feature_cols=None,
    feature_store: pd.DataFrame = None
) -> List[Dict]:
    """Rank products by query using model."""
    # Load model if not provided
    if model is None:
        model, feature_cols, _ = load_model()
    
    # Load feature store if not provided
    if feature_store is None:
        feature_store = load_feature_store()
    
    # Prepare features
    product_features = prepare_features_for_ranking(query, products, feature_store)
    
    # Select feature columns
    available_cols = [col for col in feature_cols if col in product_features.columns]
    X = product_features[available_cols].fillna(0)
    
    # Get predictions
    scores = model.predict(X)
    
    # Create results
    results = []
    for idx, (product_id, score) in enumerate(zip(product_features["product_id"], scores)):
        product = next((p for p in products if p["id"] == product_id), {})
        results.append({
            "id": int(product_id),
            "score": float(score),
            "title": product.get("title", ""),
        })
    
    # Sort by score (descending)
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results

