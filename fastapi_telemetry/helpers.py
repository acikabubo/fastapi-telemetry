"""
Prometheus metric registration helpers.

These helpers prevent ``ValueError: Duplicated timeseries`` errors that occur
when uvicorn restarts the ASGI application with ``--reload``.  Each function
looks up the metric in a module-level registry dict first; if absent it
creates and registers a new metric.  This avoids accessing private
``prometheus_client`` internals that may change across library versions.
"""

from prometheus_client import REGISTRY, Counter, Gauge, Histogram

_registry: dict[str, Counter | Gauge | Histogram] = {}


def _clear_registry(*names: str) -> None:
    """Unregister named metrics from both the module cache and Prometheus REGISTRY.

    Intended for test teardown only.
    """
    for name in names:
        collector = _registry.pop(name, None)
        if collector is not None:
            try:
                REGISTRY.unregister(collector)
            except ValueError:
                pass


def get_or_create_counter(
    name: str,
    doc: str,
    labels: list[str] | None = None,
) -> Counter:
    """
    Return a :class:`~prometheus_client.Counter`, creating it if needed.

    Args:
        name: Metric name (e.g. ``"http_requests_total"``).
        doc:  Human-readable description shown in ``/metrics``.
        labels: Optional list of label names (e.g. ``["method", "endpoint"]``).

    Returns:
        Counter instance (new or pre-existing).

    Example::

        requests_total = get_or_create_counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "status"],
        )
        requests_total.labels(method="GET", status="200").inc()
    """
    if name not in _registry:
        _registry[name] = Counter(name, doc, labels or [])
    return _registry[name]  # type: ignore[return-value]


def get_or_create_gauge(
    name: str,
    doc: str,
    labels: list[str] | None = None,
) -> Gauge:
    """
    Return a :class:`~prometheus_client.Gauge`, creating it if needed.

    Args:
        name: Metric name.
        doc:  Human-readable description.
        labels: Optional list of label names.

    Returns:
        Gauge instance (new or pre-existing).
    """
    if name not in _registry:
        _registry[name] = Gauge(name, doc, labels or [])
    return _registry[name]  # type: ignore[return-value]


def get_or_create_histogram(
    name: str,
    doc: str,
    labels: list[str] | None = None,
    buckets: list[float] | tuple[float, ...] | tuple[int, ...] | None = None,
) -> Histogram:
    """
    Return a :class:`~prometheus_client.Histogram`, creating it if needed.

    Args:
        name:    Metric name.
        doc:     Human-readable description.
        labels:  Optional list of label names.
        buckets: Optional histogram bucket boundaries.

    Returns:
        Histogram instance (new or pre-existing).
    """
    if name not in _registry:
        if buckets:
            _registry[name] = Histogram(name, doc, labels or [], buckets=buckets)
        else:
            _registry[name] = Histogram(name, doc, labels or [])
    return _registry[name]  # type: ignore[return-value]
