"""Test events data schema and invariants."""
import pytest
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import EVENTS_FILE


@pytest.mark.integration
def test_events_schema_basic():
    """Test that events have required columns and valid data."""
    if not EVENTS_FILE.exists():
        pytest.skip(f"Events file not found: {EVENTS_FILE}")
    
    df = pd.read_csv(EVENTS_FILE)
    
    # Required columns
    required = {
        "event_id", "user_id", "product_id", "query",
        "event_type", "clicked", "add_to_cart", "purchased", "timestamp"
    }
    assert required.issubset(df.columns), f"Missing columns: {required - set(df.columns)}"
    
    # event_id must be unique and non-null
    assert df["event_id"].notnull().all(), "event_id contains nulls"
    assert df["event_id"].is_unique, "event_id is not unique"
    
    # event_type must be valid
    valid_event_types = {"view", "click", "add_to_cart", "purchase"}
    assert df["event_type"].isin(valid_event_types).all(), \
        f"Invalid event types: {set(df['event_type']) - valid_event_types}"
    
    # Boolean columns must be boolean
    assert df["clicked"].dtype == bool or df["clicked"].isin([0, 1]).all(), "clicked must be boolean"
    assert df["add_to_cart"].dtype == bool or df["add_to_cart"].isin([0, 1]).all(), "add_to_cart must be boolean"
    assert df["purchased"].dtype == bool or df["purchased"].isin([0, 1]).all(), "purchased must be boolean"
    
    # timestamp must be parseable
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    assert df["timestamp"].notnull().all(), "timestamp contains invalid dates"


@pytest.mark.integration
def test_events_invariants():
    """Test events data invariants."""
    if not EVENTS_FILE.exists():
        pytest.skip(f"Events file not found: {EVENTS_FILE}")
    
    df = pd.read_csv(EVENTS_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Event funnel logic: if purchased, must have clicked and add_to_cart
    purchased_events = df[df["purchased"] == True]
    if len(purchased_events) > 0:
        assert (purchased_events["clicked"] == True).all(), \
            "Purchased events must have clicked=True"
        assert (purchased_events["add_to_cart"] == True).all(), \
            "Purchased events must have add_to_cart=True"
    
    # If add_to_cart, must have clicked
    atc_events = df[df["add_to_cart"] == True]
    if len(atc_events) > 0:
        assert (atc_events["clicked"] == True).all(), \
            "add_to_cart events must have clicked=True"
    
    # Event type should match boolean flags
    assert (df[df["event_type"] == "purchase"]["purchased"] == True).all(), \
        "purchase events should have purchased=True"
    
    # Should have events from multiple users
    assert df["user_id"].nunique() > 1, "Should have events from multiple users"
    
    # Should have events for multiple products
    assert df["product_id"].nunique() > 1, "Should have events for multiple products"
    
    # Timestamps should be in reasonable range (not too far in future, not too old)
    now = pd.Timestamp.now()
    # Allow some tolerance for timezone/timing issues (1 day buffer)
    assert (df["timestamp"] <= now + pd.Timedelta(days=1)).all(), \
        "Events should not be more than 1 day in the future"
    assert (df["timestamp"] >= now - pd.Timedelta(days=365)).all(), \
        "Events should not be older than 1 year"

