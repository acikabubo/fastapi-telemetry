"""
Circuit breaker Prometheus metrics listener.

Provides a :class:`CircuitBreakerMetricsListener` that plugs into
``pybreaker.CircuitBreaker`` and records state changes and failures as
Prometheus metrics.

Requires the ``circuit-breaker`` extra::

    pip install fastapi-telemetry[circuit-breaker]
"""

import logging
from typing import Any, Callable

from pybreaker import CircuitBreaker, CircuitBreakerListener, CircuitBreakerState

from fastapi_telemetry.helpers import get_or_create_counter, get_or_create_gauge

logger = logging.getLogger(__name__)

# ── Generic circuit-breaker metrics (defined here so they travel with the package) ──

#: Current state: 0 = closed, 1 = open, 2 = half-open
circuit_breaker_state = get_or_create_gauge(
    "circuit_breaker_state",
    "Current circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["service"],
)

#: Total number of state transitions
circuit_breaker_state_changes_total = get_or_create_counter(
    "circuit_breaker_state_changes_total",
    "Total circuit breaker state changes",
    ["service", "from_state", "to_state"],
)

#: Total number of failures recorded by the circuit breaker
circuit_breaker_failures_total = get_or_create_counter(
    "circuit_breaker_failures_total",
    "Total circuit breaker failures",
    ["service"],
)


class CircuitBreakerMetricsListener(CircuitBreakerListener):  # type: ignore[misc]
    """
    ``pybreaker`` listener that updates Prometheus metrics on circuit state changes.

    Inject it into any :class:`pybreaker.CircuitBreaker` to get automatic
    Prometheus tracking without coupling your circuit breaker code to a
    project-specific metrics facade.

    Args:
        service_name: Label value used in all metric labels
            (e.g. ``"redis"``, ``"keycloak"``).

    Example::

        from pybreaker import CircuitBreaker
        from fastapi_telemetry import CircuitBreakerMetricsListener

        redis_breaker = CircuitBreaker(
            name="redis",
            listeners=[CircuitBreakerMetricsListener(service_name="redis")],
        )
    """

    def __init__(self, service_name: str) -> None:
        """
        Initialise the listener.

        Args:
            service_name: Service label applied to all metrics.
        """
        self.service_name = service_name

    def before_call(
        self,
        _cb: CircuitBreaker,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """No-op — required by the ``CircuitBreakerListener`` interface."""

    def success(self, _cb: CircuitBreaker) -> None:
        """No-op — required by the ``CircuitBreakerListener`` interface."""

    def failure(self, _cb: CircuitBreaker, exc: BaseException) -> None:
        """
        Increment the failure counter and log the error.

        Args:
            _cb: The circuit breaker instance (unused).
            exc: The exception that triggered the failure.
        """
        logger.error(f"{self.service_name.capitalize()} circuit breaker failure: {exc}")
        circuit_breaker_failures_total.labels(service=self.service_name).inc()

    def state_change(
        self,
        _cb: CircuitBreaker,
        old_state: CircuitBreakerState | None,
        new_state: CircuitBreakerState,
    ) -> None:
        """
        Update the state gauge and increment the state-changes counter.

        Args:
            _cb:       The circuit breaker instance (unused).
            old_state: Previous state, or ``None`` on first initialisation.
            new_state: The new state.
        """
        old_name = old_state.name if old_state else "unknown"
        new_name = new_state.name

        logger.warning(
            f"{self.service_name.capitalize()} circuit breaker state changed: "
            f"{old_name} → {new_name}"
        )

        state_mapping = {"closed": 0, "open": 1, "half_open": 2}
        circuit_breaker_state.labels(service=self.service_name).set(
            state_mapping.get(new_name, 0)
        )
        circuit_breaker_state_changes_total.labels(
            service=self.service_name,
            from_state=old_name,
            to_state=new_name,
        ).inc()
