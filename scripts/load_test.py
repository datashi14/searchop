"""Load testing script for ranking API."""
import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Sample request payload
SAMPLE_REQUEST = {
    "query": "running shoes",
    "user_id": "load-test-user",
    "products": [
        {"id": i, "title": f"Product {i}", "price": 99.99, "category": "sports_outdoors"}
        for i in range(1, 21)  # 20 products
    ]
}


def make_request() -> Dict:
    """Make a single ranking request."""
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/rank",
            json=SAMPLE_REQUEST,
            timeout=5
        )
        latency = time.time() - start
        
        return {
            "success": response.status_code == 200,
            "latency": latency,
            "status_code": response.status_code,
            "error": None
        }
    except Exception as e:
        latency = time.time() - start
        return {
            "success": False,
            "latency": latency,
            "status_code": None,
            "error": str(e)
        }


def run_load_test(num_requests: int = 100, concurrency: int = 10) -> Dict:
    """Run load test with specified concurrency."""
    print(f"Running load test: {num_requests} requests, {concurrency} concurrent")
    print(f"Target: {BASE_URL}/rank")
    print()
    
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request) for _ in range(num_requests)]
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            if i % 10 == 0:
                print(f"Completed {i}/{num_requests} requests...")
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    latencies = [r["latency"] for r in successful]
    
    stats = {
        "total_requests": num_requests,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / num_requests * 100,
        "total_time": total_time,
        "requests_per_second": num_requests / total_time,
        "latency": {
            "mean": statistics.mean(latencies) if latencies else 0,
            "median": statistics.median(latencies) if latencies else 0,
            "p50": statistics.median(latencies) if latencies else 0,
            "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 1 else 0,
            "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) > 1 else 0,
            "min": min(latencies) if latencies else 0,
            "max": max(latencies) if latencies else 0,
        },
        "errors": [r["error"] for r in failed if r["error"]]
    }
    
    return stats


def print_results(stats: Dict):
    """Print load test results."""
    print("=" * 60)
    print("Load Test Results")
    print("=" * 60)
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success Rate: {stats['success_rate']:.2f}%")
    print()
    print(f"Total Time: {stats['total_time']:.2f}s")
    print(f"Requests/Second: {stats['requests_per_second']:.2f}")
    print()
    print("Latency Statistics:")
    print(f"  Mean:   {stats['latency']['mean']*1000:.2f}ms")
    print(f"  Median: {stats['latency']['median']*1000:.2f}ms")
    print(f"  P50:    {stats['latency']['p50']*1000:.2f}ms")
    print(f"  P95:    {stats['latency']['p95']*1000:.2f}ms")
    print(f"  P99:    {stats['latency']['p99']*1000:.2f}ms")
    print(f"  Min:    {stats['latency']['min']*1000:.2f}ms")
    print(f"  Max:    {stats['latency']['max']*1000:.2f}ms")
    print()
    
    if stats['errors']:
        print("Errors:")
        for error in set(stats['errors']):
            print(f"  - {error}")
    
    # Check SLO
    p95_ms = stats['latency']['p95'] * 1000
    if p95_ms < 50:
        print("✅ Latency SLO met: P95 < 50ms")
    else:
        print(f"⚠️  Latency SLO not met: P95 = {p95_ms:.2f}ms (target: <50ms)")


def main():
    """Run load test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load test ranking API")
    parser.add_argument("--requests", type=int, default=100, help="Number of requests")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--url", type=str, default=BASE_URL, help="API base URL")
    
    args = parser.parse_args()
    
    global BASE_URL
    BASE_URL = args.url
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print(f"❌ API health check failed: {response.status_code}")
            return 1
    except Exception as e:
        print(f"❌ Cannot connect to API at {BASE_URL}")
        print(f"   Error: {e}")
        print(f"\nMake sure the API is running:")
        print(f"   uvicorn src.api.main:app --reload")
        return 1
    
    print("✅ API is running")
    print()
    
    # Run load test
    stats = run_load_test(args.requests, args.concurrency)
    print_results(stats)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


