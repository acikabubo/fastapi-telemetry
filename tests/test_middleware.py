"""Tests for PrometheusMiddleware."""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from fastapi_telemetry import PrometheusMiddleware


def make_app(
    start_cb: object = None,
    end_cb: object = None,
    error_cb: object = None,
    raise_exc: bool = False,
) -> FastAPI:
    _app = FastAPI()
    _app.add_middleware(
        PrometheusMiddleware,
        request_start_callback=start_cb,  # type: ignore[arg-type]
        request_end_callback=end_cb,  # type: ignore[arg-type]
        error_callback=error_cb,  # type: ignore[arg-type]
    )

    @_app.get("/")
    async def root(_request: Request) -> PlainTextResponse:
        if raise_exc:
            raise RuntimeError("boom")
        return PlainTextResponse("ok")

    return _app


@pytest.mark.asyncio
async def test_request_start_callback_called() -> None:
    on_start = MagicMock()
    app = make_app(start_cb=on_start)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/")

    on_start.assert_called_once_with("GET", "/")


@pytest.mark.asyncio
async def test_request_end_callback_called_with_status_and_duration() -> None:
    on_end = MagicMock()
    app = make_app(end_cb=on_end)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/")

    on_end.assert_called_once()
    method, path, status, duration = on_end.call_args[0]
    assert method == "GET"
    assert path == "/"
    assert status == 200
    assert duration >= 0.0


@pytest.mark.asyncio
async def test_no_callback_does_not_raise() -> None:
    app = make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_error_callback_called_on_exception() -> None:
    on_end = MagicMock()
    on_error = MagicMock()

    _app = FastAPI()
    _app.add_middleware(
        PrometheusMiddleware,
        request_end_callback=on_end,
        error_callback=on_error,
    )

    @_app.get("/boom")
    async def boom(_request: Request) -> PlainTextResponse:
        raise RuntimeError("test error")

    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as client:
        try:
            await client.get("/boom")
        except RuntimeError:
            pass

    on_error.assert_called_once_with("RuntimeError", "/boom")
    # end callback should be called with status 500
    assert on_end.call_args[0][2] == 500
