# app/monitoring.py
import time
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from functools import wraps
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("ai-pr-reviewer")

# Metrics
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'api_active_requests',
    'Number of active requests'
)

AI_REVIEW_COUNT = Counter(
    'ai_reviews_total',
    'Total AI reviews performed',
    ['status']
)

AI_REVIEW_DURATION = Histogram(
    'ai_review_duration_seconds',
    'AI review processing time'
)

GITHUB_API_CALLS = Counter(
    'github_api_calls_total',
    'Total GitHub API calls',
    ['status']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track request metrics."""

    async def dispatch(self, request: Request, call_next):
        ACTIVE_REQUESTS.inc()
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        ACTIVE_REQUESTS.dec()

        return response


def track_ai_review(func):
    """Decorator to track AI review metrics."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            AI_REVIEW_COUNT.labels(status='success').inc()
            return result
        except Exception as e:
            AI_REVIEW_COUNT.labels(status='error').inc()
            raise
        finally:
            duration = time.time() - start_time
            AI_REVIEW_DURATION.observe(duration)
    return wrapper


def get_metrics():
    """Return Prometheus metrics."""
    return generate_latest()