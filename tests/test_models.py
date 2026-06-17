import json
from pathlib import Path

from app.models import Flight, flight_from_raw, translate_status

FIX = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIX / name).read_text())["flights"]


def test_translate_status_known():
    assert translate_status("Avgått") == "Departed"
    assert translate_status("Landat") == "Landed"
    assert translate_status("Försenad") == "Delayed"
    assert translate_status("Inställd") == "Cancelled"


def test_translate_status_unknown_returns_input():
    assert translate_status("Något") == "Något"


def test_flight_from_raw_departure_maps_fields():
    raw = load("departures_arn.json")[0]
    f = flight_from_raw(raw, direction="departure", airport="ARN")
    assert isinstance(f, Flight)
    assert f.flightNumber == "SK1401"
    assert f.airline == "SAS"
    assert f.direction == "departure"
    assert f.airport == "ARN"
    assert f.otherAirport == "CPH"
    assert f.scheduledTime == "2026-06-17T10:30:00Z"
    assert f.estimatedTime == "2026-06-17T10:45:00Z"
    assert f.status == "Departed"
    assert f.gate == "A12"
    assert f.terminal == "5"
    assert f.baggage is None


def test_flight_from_raw_arrival_includes_baggage():
    raw = load("arrivals_arn.json")[0]
    f = flight_from_raw(raw, direction="arrival", airport="ARN")
    assert f.direction == "arrival"
    assert f.otherAirport == "CPH"
    assert f.status == "Landed"
    assert f.baggage is not None
    assert f.baggage.belt == "3"
    assert f.baggage.firstBag == "2026-06-17T11:20:00Z"
    assert f.baggage.lastBag == "2026-06-17T11:35:00Z"
