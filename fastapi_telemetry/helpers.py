"""
Prometheus metric registration helpers.

These helpers prevent ``ValueError: Duplicated timeseries`` errors that occur
when uvicorn restarts the ASGI application with ``--reload``.  Each function
first tries to register a new metric; on failure it retrieves the already-
registered metric from the Prometheus registry.
"""

from prometheus_client import REGISTRY, Counter, Gauge, Histogram


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
    try:
        return Counter(name, doc, labels or [])
    except ValueError:
        return REGISTRY._names_to_collectors[name]  # type: ignore[return-value]


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
    try:
        return Gauge(name, doc, labels or [])
    except ValueError:
        return REGISTRY._names_to_collectors[name]  # type: ignore[return-value]


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
    try:
        if buckets:
            return Histogram(name, doc, labels or [], buckets=buckets)
        return Histogram(name, doc, labels or [])
    except ValueError:
        return REGISTRY._names_to_collectors[name]  # type: ignore[return-value]
