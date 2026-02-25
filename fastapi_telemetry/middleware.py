"""
Prometheus HTTP metrics middleware.

Tracks request counts, durations, and in-progress requests via injectable
callbacks so the middleware has no dependency on any app-specific metrics
facade.
"""

import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class PrometheusMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
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
        """Initialise the middleware with optional metric callbacks."""
        super().__init__(app)
        self._on_start = request_start_callback
        self._on_end = request_end_callback
        self._on_error = error_callback

    async def dispatch(self, request: Request, call_next: ASGIApp) -> Response:
        """
        Process the request and invoke metric callbacks.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or endpoint handler.

        Returns:
            HTTP response from the endpoint.
        """
        method = request.method
        path = request.url.path

        if self._on_start:
            self._on_start(method, path)

        start = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start

            if self._on_end:
                self._on_end(method, path, response.status_code, duration)

            return response

        except Exception as exc:
            duration = time.time() - start

            if self._on_end:
                self._on_end(method, path, 500, duration)
            if self._on_error:
                self._on_error(type(exc).__name__, path)

            raise exc
