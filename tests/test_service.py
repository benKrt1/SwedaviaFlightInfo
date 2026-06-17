import json
from pathlib import Path

import pytest

from app import service
from app.cache import TTLCache
from app.models import Flight

FIX = Path(__file__).parent / "fixtures"


def raw_departures():
    return json.loads((FIX / "departures_arn.json").read_text())["flights"]


@pytest.fixture(autouse=True)
def reset_cache():
    service._cache = TTLCache(ttl_seconds=60)
    yield


async def test_get_flights_maps_to_flight_models(monkeypatch):
    async def fake_fetch(airport, direction, date):
        return raw_departures()

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    flights = await service.get_flights("ARN", "departure", "2026-06-17")
    assert len(flights) == 1
    assert flights[0].flightNumber == "SK1401"
    assert flights[0].status == "Departed"


async def test_get_flights_uses_cache_on_second_call(monkeypatch):
    calls = {"n": 0}

    async def fake_fetch(airport, direction, date):
        calls["n"] += 1
        return raw_departures()

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    await service.get_flights("ARN", "departure", "2026-06-17")
    await service.get_flights("ARN", "departure", "2026-06-17")
    assert calls["n"] == 1  # second call served from cache


def test_filter_by_status():
    flights = [
        Flight(direction="departure", airport="ARN", status="Delayed"),
        Flight(direction="departure", airport="ARN", status="On time"),
    ]
    result = service.filter_flights(flights, status="delayed")
    assert len(result) == 1
    assert result[0].status == "Delayed"


def test_filter_by_destination():
    flights = [
        Flight(direction="departure", airport="ARN", otherAirport="CPH"),
        Flight(direction="departure", airport="ARN", otherAirport="LHR"),
    ]
    result = service.filter_flights(flights, destination="cph")
    assert len(result) == 1
    assert result[0].otherAirport == "CPH"


def test_search_by_flight_number():
    flights = [
        Flight(direction="departure", airport="ARN", flightNumber="SK1401"),
        Flight(direction="departure", airport="ARN", flightNumber="DY1234"),
    ]
    result = service.search_flight(flights, "sk1401")
    assert result is not None
    assert result.flightNumber == "SK1401"
