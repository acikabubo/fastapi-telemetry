# fastapi-telemetry

> **Name reserved — active development coming soon.**

Prometheus metrics middleware, circuit breaker listener, and metric helpers for FastAPI.

## Planned Features

- `PrometheusMiddleware` — HTTP request duration, count, and in-flight metrics out of the box
- `CircuitBreakerMetricsListener` — pybreaker listener that exports circuit breaker state to Prometheus
- Pre-built metric helpers — labelled counters and histograms for common patterns (auth attempts, cache hits, WS messages)
- `/metrics` endpoint integration — drop-in Prometheus scrape endpoint
- Optional `prometheus-client` and `pybreaker` extras (core package has zero dependencies)

## Status

This package is a name reservation. Implementation will follow.

Follow progress at: https://github.com/acikabubo/fastapi-telemetry

## License

MIT
