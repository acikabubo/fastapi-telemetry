"""Tests for get_or_create_counter/gauge/histogram helpers."""

import pytest
from prometheus_client import Counter, Gauge, Histogram

from fastapi_telemetry import get_or_create_counter, get_or_create_gauge, get_or_create_histogram
from fastapi_telemetry.helpers import _clear_registry

_TEST_NAMES = (
    "test_counter_total",
    "test_gauge",
    "test_histogram",
    "test_labeled_counter_total",
)


@pytest.fixture(autouse=True)
def _cleanup() -> None:
    _clear_registry(*_TEST_NAMES)
    yield
    _clear_registry(*_TEST_NAMES)


def test_creates_counter() -> None:
    counter = get_or_create_counter("test_counter_total", "A test counter")
    assert isinstance(counter, Counter)


def test_creates_gauge() -> None:
    gauge = get_or_create_gauge("test_gauge", "A test gauge")
    assert isinstance(gauge, Gauge)


def test_creates_histogram() -> None:
    histogram = get_or_create_histogram("test_histogram", "A test histogram")
    assert isinstance(histogram, Histogram)


def test_counter_returns_existing_on_duplicate() -> None:
    first = get_or_create_counter("test_counter_total", "A test counter")
    second = get_or_create_counter("test_counter_total", "A test counter")
    # Both should refer to the same underlying collector
    assert first._name == second._name  # type: ignore[attr-defined]


def test_counter_with_labels() -> None:
    counter = get_or_create_counter(
        "test_labeled_counter_total", "Labeled counter", ["method", "status"]
    )
    counter.labels(method="GET", status="200").inc()
    assert isinstance(counter, Counter)


def test_histogram_with_custom_buckets() -> None:
    histogram = get_or_create_histogram(
        "test_histogram", "A test histogram", buckets=[0.1, 0.5, 1.0]
    )
    assert isinstance(histogram, Histogram)
