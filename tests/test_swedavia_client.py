import httpx
import pytest
import respx

from app.swedavia_client import SwedaviaUnavailable, fetch_flights

BASE = "https://api.swedavia.se/flightinfo/v2"


@respx.mock
async def test_fetch_flights_builds_url_and_header(monkeypatch):
    monkeypatch.setenv("SWEDAVIA_API_KEY", "key-abc")
    route = respx.get(f"{BASE}/ARN/departures/2026-06-17").mock(
        return_value=httpx.Response(200, json={"flights": [{"flightId": "SK1"}]})
    )
    result = await fetch_flights("ARN", "departure", "2026-06-17")
    assert route.called
    assert route.calls.last.request.headers["Ocp-Apim-Subscription-Key"] == "key-abc"
    assert result == [{"flightId": "SK1"}]


@respx.mock
async def test_fetch_flights_arrival_path(monkeypatch):
    monkeypatch.setenv("SWEDAVIA_API_KEY", "key-abc")
    route = respx.get(f"{BASE}/GOT/arrivals/2026-06-17").mock(
        return_value=httpx.Response(200, json={"flights": []})
    )
    await fetch_flights("GOT", "arrival", "2026-06-17")
    assert route.called


@respx.mock
async def test_fetch_flights_upstream_500_raises(monkeypatch):
    monkeypatch.setenv("SWEDAVIA_API_KEY", "key-abc")
    respx.get(f"{BASE}/ARN/departures/2026-06-17").mock(
        return_value=httpx.Response(500)
    )
    with pytest.raises(SwedaviaUnavailable):
        await fetch_flights("ARN", "departure", "2026-06-17")


@respx.mock
async def test_fetch_flights_timeout_raises(monkeypatch):
    monkeypatch.setenv("SWEDAVIA_API_KEY", "key-abc")
    respx.get(f"{BASE}/ARN/departures/2026-06-17").mock(
        side_effect=httpx.ConnectTimeout("timeout")
    )
    with pytest.raises(SwedaviaUnavailable):
        await fetch_flights("ARN", "departure", "2026-06-17")
