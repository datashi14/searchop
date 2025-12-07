"""Monitoring and metrics."""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
import time

# Metrics
request_count = Counter(
    "rank_requests_total",
    "Total number of ranking requests",
    ["status"]
)

request_latency = Histogram(
    "rank_request_duration_seconds",
    "Ranking request latency",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

model_version = Gauge(
    "model_version_info",
    "Current model version",
    ["version"]
)

active_requests = Gauge(
    "rank_active_requests",
    "Number of active ranking requests"
)


def get_metrics():
    """Get Prometheus metrics."""
    return generate_latest()


def get_metrics_content_type():
    """Get Prometheus metrics content type."""
    return CONTENT_TYPE_LATEST

