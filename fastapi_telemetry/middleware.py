"""
Prometheus HTTP metrics middleware.

Tracks request counts, durations, and in-progress requests via injectable
callbacks so the middleware has no dependency on any app-specific metrics
facade.

Implemented as a pure ASGI middleware (not ``BaseHTTPMiddleware``) to avoid
buffering streaming responses in memory.
"""

import time
from collections.abc import Callable

from starlette.types import ASGIApp, Receive, Scope, Send


class PrometheusMiddleware:
    """
    ASGI middleware that records Prometheus HTTP metrics.

    All recording is delegated to user-supplied callbacks so the middleware
    carries no dependency on a specific metrics backend or facade.

    Args:
        app: The ASGI application.
        request_start_callback: Called with ``(method, path)`` when a request
            arrives.  Use it to increment an in-progress gauge.
        request_end_callback: Called with ``(method, path, status_code,
            duration_seconds)`` when a response is produced.
        error_callback: Called with ``(error_type, path)`` when an unhandled
            exception is raised during request processing.

    Example::

        from fastapi_telemetry import PrometheusMiddleware
        from app.utils.metrics import MetricsCollector

        app.add_middleware(
            PrometheusMiddleware,
            request_start_callback=MetricsCollector.record_http_request_start,
            request_end_callback=MetricsCollector.record_http_request_end,
            error_callback=MetricsCollector.record_app_error,
        )
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        request_start_callback: Callable[[str, str], None] | None = None,
        request_end_callback: Callable[[str, str, int, float], None] | None = None,
        error_callback: Callable[[str, str], None] | None = None,
    ) -> None:
        self.app = app
        self._on_start = request_start_callback
        self._on_end = request_end_callback
        self._on_error = error_callback

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Process the request and invoke metric callbacks.

        Non-HTTP scopes (WebSocket, lifespan) are passed through unchanged.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]

        if self._on_start:
            self._on_start(method, path)

        status_code = 500

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        start = time.monotonic()
        try:
            await self.app(scope, receive, send_wrapper)
            if self._on_end:
                self._on_end(method, path, status_code, time.monotonic() - start)
        except Exception as exc:
            if self._on_end:
                self._on_end(method, path, 500, time.monotonic() - start)
            if self._on_error:
                self._on_error(type(exc).__name__, path)
            raise
