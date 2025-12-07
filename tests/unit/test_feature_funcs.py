"""Test feature engineering functions."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_ingestion.build_feature_store import (
    compute_product_features,
    compute_query_product_features,
    compute_tfidf_similarity,
)


def test_compute_tfidf_similarity():
    """Test TF-IDF similarity computation."""
    # Exact match
    assert compute_tfidf_similarity("running shoes", "running shoes") == 1.0
    
    # Partial match
    similarity = compute_tfidf_similarity("running shoes", "Nike running shoes")
    assert 0.0 < similarity < 1.0
    
    # No match
    assert compute_tfidf_similarity("laptop", "running shoes") == 0.0
    
    # Empty strings
    assert compute_tfidf_similarity("", "test") == 0.0
    assert compute_tfidf_similarity("test", "") == 0.0


def test_compute_product_features(sample_catalog, sample_events):
    """Test product feature computation."""
    features = compute_product_features(sample_catalog, sample_events)
    
    # Check required columns exist
    required_cols = [
        "product_id", "ctr", "atc_rate", "purchase_rate",
        "recent_views_7d", "recent_purchases_7d", "popularity"
    ]
    for col in required_cols:
        assert col in features.columns, f"Missing column: {col}"
    
    # Check all products are present
    assert len(features) == len(sample_catalog)
    assert set(features["product_id"]) == set(sample_catalog["product_id"])
    
    # Check rates are between 0 and 1
    assert (features["ctr"] >= 0).all() and (features["ctr"] <= 1).all()
    assert (features["atc_rate"] >= 0).all() and (features["atc_rate"] <= 1).all()
    assert (features["purchase_rate"] >= 0).all() and (features["purchase_rate"] <= 1).all()
    
    # Check popularity is normalized (0-1)
    assert (features["popularity"] >= 0).all() and (features["popularity"] <= 1).all()
    
    # Check recency features are non-negative
    assert (features["recent_views_7d"] >= 0).all()
    assert (features["recent_purchases_7d"] >= 0).all()


def test_compute_query_product_features(sample_events, sample_catalog):
    """Test query-product feature computation."""
    product_features = compute_product_features(sample_catalog, sample_events)
    query_product_features = compute_query_product_features(sample_events, product_features)
    
    # Check required columns
    required_cols = [
        "query", "product_id", "query_ctr", "query_purchase_rate"
    ]
    for col in required_cols:
        assert col in query_product_features.columns, f"Missing column: {col}"
    
    # Check rates are valid
    assert (query_product_features["query_ctr"] >= 0).all()
    assert (query_product_features["query_ctr"] <= 1).all()
    assert (query_product_features["query_purchase_rate"] >= 0).all()
    assert (query_product_features["query_purchase_rate"] <= 1).all()
    
    # Check we have query-product pairs
    assert len(query_product_features) > 0
    assert "query" in query_product_features.columns
    assert "product_id" in query_product_features.columns

