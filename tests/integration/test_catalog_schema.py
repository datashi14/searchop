"""Test catalog data schema and invariants."""
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import CATALOG_FILE  # noqa: E402


@pytest.mark.integration
def test_catalog_schema_basic():
    """Test that catalog has required columns and valid data."""
    if not CATALOG_FILE.exists():
        pytest.skip(f"Catalog file not found: {CATALOG_FILE}")
    
    df = pd.read_csv(CATALOG_FILE)
    
    # Required columns
    required = {"product_id", "title", "description", "category", "price", "brand", "rating", "tags"}
    assert required.issubset(df.columns), f"Missing columns: {required - set(df.columns)}"
    
    # product_id must be unique and non-null
    assert df["product_id"].notnull().all(), "product_id contains nulls"
    assert df["product_id"].is_unique, "product_id is not unique"
    
    # title must be non-null
    assert df["title"].notnull().all(), "title contains nulls"
    
    # category must be non-null
    assert df["category"].notnull().all(), "category contains nulls"
    
    # price must be positive
    assert (df["price"] > 0).all(), "price contains non-positive values"
    
    # rating must be between 0 and 5
    assert (df["rating"] >= 0).all() and (df["rating"] <= 5).all(), "rating out of range [0, 5]"


@pytest.mark.integration
def test_catalog_invariants():
    """Test catalog data invariants."""
    if not CATALOG_FILE.exists():
        pytest.skip(f"Catalog file not found: {CATALOG_FILE}")
    
    df = pd.read_csv(CATALOG_FILE)
    
    # At least some products should exist
    assert len(df) > 0, "Catalog is empty"
    
    # product_id should be sequential or at least start from 1
    assert df["product_id"].min() >= 1, "product_id should start from 1"
    
    # Should have multiple categories
    assert df["category"].nunique() > 1, "Should have multiple categories"
    
    # Price distribution should be reasonable (no extreme outliers)
    price_q99 = df["price"].quantile(0.99)
    price_q01 = df["price"].quantile(0.01)
    assert price_q99 / price_q01 < 1000, "Price range too extreme (possible data issue)"

