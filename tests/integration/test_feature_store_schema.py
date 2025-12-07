"""Test feature store schema and invariants."""
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import FEATURE_STORE_FILE  # noqa: E402


@pytest.mark.integration
def test_feature_store_schema_basic():
    """Test that feature store has required columns."""
    if not FEATURE_STORE_FILE.exists():
        pytest.skip(f"Feature store file not found: {FEATURE_STORE_FILE}")
    
    df = pd.read_parquet(FEATURE_STORE_FILE)
    
    # Required columns
    required = {
        "query", "product_id", "ctr", "atc_rate", "purchase_rate",
        "query_ctr", "query_purchase_rate", "tfidf_similarity"
    }
    assert required.issubset(df.columns), f"Missing columns: {required - set(df.columns)}"
    
    # Key identifiers must be non-null
    assert df["query"].notnull().all(), "query contains nulls"
    assert df["product_id"].notnull().all(), "product_id contains nulls"
    
    # Rates should be between 0 and 1
    rate_columns = ["ctr", "atc_rate", "purchase_rate", "query_ctr", "query_purchase_rate"]
    for col in rate_columns:
        if col in df.columns:
            assert (df[col] >= 0).all() and (df[col] <= 1).all(), \
                f"{col} out of range [0, 1]"
    
    # TF-IDF similarity should be between 0 and 1
    if "tfidf_similarity" in df.columns:
        assert (df["tfidf_similarity"] >= 0).all() and (df["tfidf_similarity"] <= 1).all(), \
            "tfidf_similarity out of range [0, 1]"


@pytest.mark.integration
def test_feature_store_invariants():
    """Test feature store data invariants."""
    if not FEATURE_STORE_FILE.exists():
        pytest.skip(f"Feature store file not found: {FEATURE_STORE_FILE}")
    
    df = pd.read_parquet(FEATURE_STORE_FILE)
    
    # Should have query-product pairs
    assert len(df) > 0, "Feature store is empty"
    
    # Should have multiple unique queries
    assert df["query"].nunique() > 1, "Should have multiple unique queries"
    
    # Should have multiple unique products
    assert df["product_id"].nunique() > 1, "Should have multiple unique products"
    
    # Query-product pairs should be unique (or at least have reasonable distribution)
    # Most pairs should appear once, but some duplicates are OK for aggregation
    
    # Rates should follow logical relationships
    # purchase_rate should generally be <= atc_rate <= ctr
    # (but not strictly, due to different time windows)
    if all(col in df.columns for col in ["ctr", "atc_rate", "purchase_rate"]):
        # Check that most rows follow the pattern (allowing for some exceptions)
        logical_rows = (df["purchase_rate"] <= df["atc_rate"]) & (df["atc_rate"] <= df["ctr"])
        assert logical_rows.sum() / len(df) > 0.7, \
            "Most rows should follow: purchase_rate <= atc_rate <= ctr"

