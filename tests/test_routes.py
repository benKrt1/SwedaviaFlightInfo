import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import service
from app.cache import TTLCache
from app.main import app
from app.swedavia_client import SwedaviaUnavailable

FIX = Path(__file__).parent / "fixtures"
client = TestClient(app)


def raw(name):
    return json.loads((FIX / name).read_text())["flights"]


@pytest.fixture(autouse=True)
def reset_cache():
    service._cache = TTLCache(ttl_seconds=60)
    yield


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_departures_ok(monkeypatch):
    async def fake_fetch(airport, direction, date):
        return raw("departures_arn.json")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    r = client.get("/flights/ARN/departures")
    assert r.status_code == 200
    body = r.json()
    assert body[0]["flightNumber"] == "SK1401"
    assert body[0]["status"] == "Departed"


def test_arrivals_includes_baggage(monkeypatch):
    async def fake_fetch(airport, direction, date):
        return raw("arrivals_arn.json")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    r = client.get("/flights/ARN/arrivals")
    assert r.status_code == 200
    assert r.json()[0]["baggage"]["belt"] == "3"


def test_invalid_airport_returns_400():
    r = client.get("/flights/XXX/departures")
    assert r.status_code == 400
    assert "ARN" in r.json()["detail"]


def test_invalid_date_returns_400():
    r = client.get("/flights/ARN/departures?date=17-06-2026")
    assert r.status_code == 400


def test_search_found(monkeypatch):
    async def fake_fetch(airport, direction, date):
        return raw("departures_arn.json")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    r = client.get("/flights/ARN/search?flight=SK1401")
    assert r.status_code == 200
    assert r.json()["flightNumber"] == "SK1401"


def test_search_not_found(monkeypatch):
    async def fake_fetch(airport, direction, date):
        return raw("departures_arn.json")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    r = client.get("/flights/ARN/search?flight=ZZ9999")
    assert r.status_code == 404


def test_status_filter(monkeypatch):
    async def fake_fetch(airport, direction, date):
        return raw("departures_arn.json")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    r = client.get("/flights/ARN/departures?status=delayed")
    assert r.status_code == 200
    assert r.json() == []  # the sample flight is "Departed", not delayed


def test_upstream_error_returns_502(monkeypatch):
    async def fake_fetch(airport, direction, date):
        raise SwedaviaUnavailable("boom")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    r = client.get("/flights/ARN/departures")
    assert r.status_code == 502


def test_missing_api_key_returns_503(monkeypatch):
    async def fake_fetch(airport, direction, date):
        raise RuntimeError("SWEDAVIA_API_KEY is not set. Add it to your .env file.")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    r = client.get("/flights/ARN/departures")
    assert r.status_code == 503
    assert "SWEDAVIA_API_KEY" in r.json()["detail"]
