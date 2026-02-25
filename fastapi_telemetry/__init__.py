"""fastapi-telemetry — Prometheus metrics middleware and circuit breaker listener for FastAPI."""

from fastapi_telemetry.helpers import (
    get_or_create_counter,
    get_or_create_gauge,
    get_or_create_histogram,
)
from fastapi_telemetry.middleware import PrometheusMiddleware

__version__ = "0.0.1"

__all__ = [
    # Middleware
    "PrometheusMiddleware",
    # Prometheus helpers
    "get_or_create_counter",
    "get_or_create_gauge",
    "get_or_create_histogram",
]

# CircuitBreakerMetricsListener is available only when pybreaker is installed
try:
    from fastapi_telemetry.circuit_breaker import CircuitBreakerMetricsListener

    __all__ += ["CircuitBreakerMetricsListener"]
except ImportError:
    pass
