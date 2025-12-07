"""Pytest configuration and fixtures."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import (
    CATALOG_FILE, EVENTS_FILE, FEATURE_STORE_FILE,
    RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR
)


@pytest.fixture
def sample_catalog():
    """Sample catalog DataFrame for testing."""
    return pd.DataFrame({
        "product_id": [1, 2, 3],
        "title": ["Nike Running Shoes", "Adidas Sneakers", "Puma Boots"],
        "description": ["Great shoes", "Comfortable", "Durable"],
        "category": ["footwear", "footwear", "footwear"],
        "price": [99.99, 79.99, 129.99],
        "brand": ["Nike", "Adidas", "Puma"],
        "rating": [4.5, 4.2, 4.8],
        "tags": ["popular,new", "bestseller", "premium"],
    })


@pytest.fixture
def sample_events():
    """Sample events DataFrame for testing."""
    base_time = datetime.now() - timedelta(days=1)
    return pd.DataFrame({
        "event_id": [1, 2, 3, 4, 5],
        "user_id": ["u-1", "u-1", "u-2", "u-2", "u-3"],
        "product_id": [1, 1, 2, 2, 3],
        "query": ["running shoes", "running shoes", "sneakers", "sneakers", "boots"],
        "event_type": ["view", "click", "view", "add_to_cart", "purchase"],
        "clicked": [False, True, False, True, True],
        "add_to_cart": [False, False, False, True, True],
        "purchased": [False, False, False, False, True],
        "timestamp": [
            base_time,
            base_time + timedelta(minutes=5),
            base_time + timedelta(hours=1),
            base_time + timedelta(hours=1, minutes=10),
            base_time + timedelta(hours=2),
        ],
    })


@pytest.fixture
def sample_feature_store(sample_catalog, sample_events):
    """Sample feature store DataFrame for testing."""
    # Simulate feature store structure
    return pd.DataFrame({
        "query": ["running shoes", "running shoes", "sneakers"],
        "product_id": [1, 2, 2],
        "title": ["Nike Running Shoes", "Adidas Sneakers", "Adidas Sneakers"],
        "category": ["footwear", "footwear", "footwear"],
        "price": [99.99, 79.99, 79.99],
        "ctr": [0.5, 0.3, 0.3],
        "atc_rate": [0.2, 0.1, 0.1],
        "purchase_rate": [0.1, 0.05, 0.05],
        "query_ctr": [0.6, 0.4, 0.4],
        "query_purchase_rate": [0.15, 0.08, 0.08],
        "tfidf_similarity": [0.8, 0.6, 0.6],
        "popularity": [0.9, 0.7, 0.7],
    })


@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary directory for test data."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()
    return tmp_path

