"""Smoke tests for ranking service."""
import pytest
import requests
import time
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def api_server():
    """Start API server for testing."""
    # Check if server is already running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            yield BASE_URL
            return
    except requests.exceptions.RequestException:
        pass
    
    # Server not running - skip E2E tests
    pytest.skip("API server not running. Start with: uvicorn src.api.main:app")


@pytest.mark.e2e
def test_health(api_server):
    """Test health endpoint."""
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert data["status"] == "healthy"


@pytest.mark.e2e
def test_metrics_endpoint(api_server):
    """Test metrics endpoint."""
    r = requests.get(f"{BASE_URL}/metrics", timeout=5)
    assert r.status_code == 200
    # Should return Prometheus metrics format
    assert "text/plain" in r.headers.get("content-type", "")


@pytest.mark.e2e
def test_rank_basic(api_server):
    """Test basic ranking endpoint."""
    payload = {
        "query": "running shoes",
        "user_id": "test-user",
        "products": [
            {
                "id": 1,
                "title": "Nike Running Shoes",
                "price": 99.99,
                "category": "footwear"
            },
            {
                "id": 2,
                "title": "Adidas Sneakers",
                "price": 79.99,
                "category": "footwear"
            },
            {
                "id": 3,
                "title": "Puma Boots",
                "price": 129.99,
                "category": "footwear"
            }
        ]
    }
    
    r = requests.post(f"{BASE_URL}/rank", json=payload, timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    
    data = r.json()
    assert "ranked_products" in data
    assert len(data["ranked_products"]) == len(payload["products"])
    
    # Check structure of ranked products
    for product in data["ranked_products"]:
        assert "id" in product
        assert "score" in product
        assert isinstance(product["score"], (int, float))
        assert 0 <= product["score"] <= 1


@pytest.mark.e2e
def test_rank_empty_products(api_server):
    """Test ranking with empty product list."""
    payload = {
        "query": "test query",
        "user_id": "test-user",
        "products": []
    }
    
    r = requests.post(f"{BASE_URL}/rank", json=payload, timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "ranked_products" in data
    assert len(data["ranked_products"]) == 0


@pytest.mark.e2e
def test_rank_invalid_request(api_server):
    """Test ranking with invalid request."""
    # Missing required fields
    invalid_payloads = [
        {},  # Empty
        {"query": "test"},  # Missing user_id and products
        {"user_id": "test"},  # Missing query and products
    ]
    
    for payload in invalid_payloads:
        r = requests.post(f"{BASE_URL}/rank", json=payload, timeout=10)
        # Should return 422 (validation error) or 400 (bad request)
        assert r.status_code in [400, 422], \
            f"Expected 400/422 for invalid payload, got {r.status_code}"


@pytest.mark.e2e
def test_rank_latency(api_server):
    """Test that ranking endpoint responds within latency SLO."""
    payload = {
        "query": "running shoes",
        "user_id": "test-user",
        "products": [
            {"id": i, "title": f"Product {i}", "price": 99.99, "category": "test"}
            for i in range(10)
        ]
    }
    
    start = time.time()
    r = requests.post(f"{BASE_URL}/rank", json=payload, timeout=10)
    latency = time.time() - start
    
    assert r.status_code == 200
    # Latency SLO: p95 < 500ms for this test
    assert latency < 0.5, f"Latency too high: {latency:.3f}s (SLO: <0.5s)"

