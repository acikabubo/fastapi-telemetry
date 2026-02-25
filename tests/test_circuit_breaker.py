"""Tests for CircuitBreakerMetricsListener."""

from unittest.mock import MagicMock, patch

import pytest
from pybreaker import CircuitBreakerState

from fastapi_telemetry.circuit_breaker import (
    CircuitBreakerMetricsListener,
    circuit_breaker_failures_total,
    circuit_breaker_state,
    circuit_breaker_state_changes_total,
)


@pytest.fixture()
def listener() -> CircuitBreakerMetricsListener:
    return CircuitBreakerMetricsListener(service_name="test_svc")


def test_failure_increments_counter(listener: CircuitBreakerMetricsListener) -> None:
    cb = MagicMock()
    before = circuit_breaker_failures_total.labels(service="test_svc")._value.get()  # type: ignore[attr-defined]
    listener.failure(cb, ValueError("db down"))
    after = circuit_breaker_failures_total.labels(service="test_svc")._value.get()  # type: ignore[attr-defined]
    assert after == before + 1


def test_state_change_updates_gauge(listener: CircuitBreakerMetricsListener) -> None:
    cb = MagicMock()
    open_state = MagicMock(spec=CircuitBreakerState)
    open_state.name = "open"

    listener.state_change(cb, None, open_state)

    val = circuit_breaker_state.labels(service="test_svc")._value.get()  # type: ignore[attr-defined]
    assert val == 1  # open = 1


def test_state_change_increments_changes_counter(
    listener: CircuitBreakerMetricsListener,
) -> None:
    cb = MagicMock()
    closed_state = MagicMock(spec=CircuitBreakerState)
    closed_state.name = "closed"
    open_state = MagicMock(spec=CircuitBreakerState)
    open_state.name = "open"

    before = (
        circuit_breaker_state_changes_total.labels(  # type: ignore[attr-defined]
            service="test_svc", from_state="closed", to_state="open"
        )
        ._value.get()
    )
    listener.state_change(cb, closed_state, open_state)
    after = (
        circuit_breaker_state_changes_total.labels(  # type: ignore[attr-defined]
            service="test_svc", from_state="closed", to_state="open"
        )
        ._value.get()
    )
    assert after == before + 1


def test_state_change_with_none_old_state(listener: CircuitBreakerMetricsListener) -> None:
    cb = MagicMock()
    closed_state = MagicMock(spec=CircuitBreakerState)
    closed_state.name = "closed"
    # Should not raise even with old_state=None
    listener.state_change(cb, None, closed_state)


def test_before_call_is_noop(listener: CircuitBreakerMetricsListener) -> None:
    cb = MagicMock()
    listener.before_call(cb, lambda: None)  # should not raise


def test_success_is_noop(listener: CircuitBreakerMetricsListener) -> None:
    cb = MagicMock()
    listener.success(cb)  # should not raise


def test_failure_logs_error(listener: CircuitBreakerMetricsListener) -> None:
    cb = MagicMock()
    with patch("fastapi_telemetry.circuit_breaker.logger") as mock_logger:
        listener.failure(cb, RuntimeError("timeout"))
    mock_logger.error.assert_called_once()
    assert "Test_svc" in mock_logger.error.call_args[0][0]
