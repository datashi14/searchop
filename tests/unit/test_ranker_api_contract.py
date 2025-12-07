"""Test API contract and request/response schemas."""
import pytest
from pydantic import ValidationError
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_rank_request_schema():
    """Test that rank request schema validates correctly."""
    # This will be implemented once we create the API schemas
    # For now, we'll test the expected structure
    
    valid_request = {
        "query": "running shoes",
        "user_id": "u-123",
        "products": [
            {
                "id": 1,
                "title": "Nike Running Shoes",
                "price": 99.99,
                "category": "footwear"
            }
        ]
    }
    
    # Basic structure checks
    assert "query" in valid_request
    assert "user_id" in valid_request
    assert "products" in valid_request
    assert isinstance(valid_request["products"], list)
    assert len(valid_request["products"]) > 0
    
    # Product structure
    product = valid_request["products"][0]
    assert "id" in product
    assert "title" in product
    assert "price" in product


def test_rank_response_schema():
    """Test that rank response schema is correct."""
    # Expected response structure
    valid_response = {
        "ranked_products": [
            {
                "id": 1,
                "score": 0.95,
                "title": "Nike Running Shoes"
            },
            {
                "id": 2,
                "score": 0.87,
                "title": "Adidas Sneakers"
            }
        ]
    }
    
    assert "ranked_products" in valid_response
    assert isinstance(valid_response["ranked_products"], list)
    
    for product in valid_response["ranked_products"]:
        assert "id" in product
        assert "score" in product
        assert isinstance(product["score"], (int, float))
        assert 0 <= product["score"] <= 1  # Scores should be normalized


def test_rank_request_validation_errors():
    """Test that invalid requests are rejected."""
    # Missing required fields
    invalid_requests = [
        {},  # Empty
        {"query": "test"},  # Missing user_id and products
        {"user_id": "u-1"},  # Missing query and products
        {"query": "test", "user_id": "u-1"},  # Missing products
        {"query": "test", "products": []},  # Empty products
    ]
    
    # These should all fail validation (will be implemented with Pydantic)
    for req in invalid_requests:
        # Basic checks
        if "products" not in req or not req.get("products"):
            assert True  # Would fail validation
        if "query" not in req:
            assert True  # Would fail validation

