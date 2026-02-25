# fastapi-telemetry

> 📢 **Hobby Project Notice:** This is a research and learning project exploring FastAPI
> observability and Prometheus metrics best practices. Feel free to use it as a reference,
> report issues, or suggest improvements! Contributions and feedback are always welcome.

Prometheus metrics middleware, circuit breaker listener, and metric helpers for FastAPI —
zero project-specific dependencies (only Starlette and `prometheus-client`).

## Features

- `PrometheusMiddleware` — HTTP request duration, count, and in-flight metrics out of the
  box via injectable callbacks (no coupling to a specific metrics facade)
- `CircuitBreakerMetricsListener` — `pybreaker` listener that exports circuit breaker
  state, state-changes, and failure counts to Prometheus (optional dependency)
- `get_or_create_counter` / `get_or_create_gauge` / `get_or_create_histogram` — safe
  helpers that return an existing metric from the registry instead of raising
  `ValueError` on duplicate registration (useful with `--reload`)

## Installation

```bash
# Core (middleware + helpers)
pip install fastapi-telemetry

# With circuit-breaker support
pip install "fastapi-telemetry[circuit-breaker]"
```

## Quick start

```python
from fastapi import FastAPI
from fastapi_telemetry import PrometheusMiddleware, CircuitBreakerMetricsListener
from prometheus_client import make_asgi_app

app = FastAPI()

# Mount Prometheus scrape endpoint
app.mount("/metrics", make_asgi_app())

# Wire up the middleware with your own metric callbacks
app.add_middleware(
    PrometheusMiddleware,
    request_start_callback=lambda method, path: None,   # replace with your gauge.inc()
    request_end_callback=lambda m, p, s, d: None,       # replace with your histogram
    error_callback=lambda error_type, path: None,       # replace with your counter.inc()
)
```

### Circuit breaker

```python
from pybreaker import CircuitBreaker
from fastapi_telemetry import CircuitBreakerMetricsListener

cb = CircuitBreaker(
    name="redis",
    listeners=[CircuitBreakerMetricsListener(service_name="redis")],
)
```

## License

MIT
