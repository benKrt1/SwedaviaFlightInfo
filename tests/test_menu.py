import json
from pathlib import Path

import pytest

from app import menu, service
from app.cache import TTLCache
from app.models import BaggageInfo, Flight

FIX = Path(__file__).parent / "fixtures"


def raw(name):
    return json.loads((FIX / name).read_text())["flights"]


@pytest.fixture(autouse=True)
def reset_cache():
    service._cache = TTLCache(ttl_seconds=60)
    yield


def _flight(number, t, **kw):
    return Flight(
        flightNumber=number, direction=kw.get("direction", "departure"),
        airport="ARN", scheduledTime=t, **{k: v for k, v in kw.items() if k != "direction"}
    )


# --- pure helpers ---

def test_sort_by_time_orders_ascending_none_last():
    flights = [
        _flight("C", "2026-06-17T12:00:00Z"),
        _flight("A", "2026-06-17T08:00:00Z"),
        _flight("N", None),
        _flight("B", "2026-06-17T10:00:00Z"),
    ]
    ordered = [f.flightNumber for f in menu.sort_by_time(flights)]
    assert ordered == ["A", "B", "C", "N"]


def test_upcoming_from_drops_past_and_sorts():
    flights = [
        _flight("PAST", "2026-06-17T08:00:00Z"),
        _flight("SOON", "2026-06-17T10:30:00Z"),
        _flight("LATER", "2026-06-17T15:00:00Z"),
    ]
    result = menu.upcoming_from(flights, "2026-06-17T10:00:00Z")
    assert [f.flightNumber for f in result] == ["SOON", "LATER"]


def test_render_baggage_has_columns_and_values():
    flights = [
        _flight(
            "SK1402", "2026-06-17T11:00:00Z", direction="arrival",
            otherAirport="CPH",
            baggage=BaggageInfo(
                belt="3", firstBag="2026-06-17T11:20:00Z",
                lastBag="2026-06-17T11:35:00Z",
            ),
        )
    ]
    out = menu.render_baggage(flights)
    assert "Flight" in out and "From" in out and "Belt" in out
    assert "First" in out and "Last" in out
    assert "SK1402" in out and "CPH" in out and "3" in out
    assert "11:20" in out and "11:35" in out


def test_render_baggage_empty():
    assert menu.render_baggage([]) == "No flights found."


# --- interactive loop ---

def _fake_input(answers):
    it = iter(answers)
    return lambda prompt="": next(it)


async def test_menu_departures_then_quit(monkeypatch, capsys):
    async def fake_fetch(airport, direction, date):
        return raw("departures_arn.json")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    # airport (Enter=ARN), choose 2 (departures), q to quit pagination, q to exit menu
    await menu.main_async(
        inputs=_fake_input(["", "2", "q"]),
        now_iso="2026-06-17T00:00:00Z",
    )
    out = capsys.readouterr().out
    assert "SK1401" in out
    assert "Flight" in out


async def test_menu_quit_at_airport_prompt(capsys):
    await menu.main_async(inputs=_fake_input(["q"]), now_iso="2026-06-17T00:00:00Z")
    # exits cleanly without error
    assert True


async def test_menu_invalid_airport_reprompts(monkeypatch, capsys):
    async def fake_fetch(airport, direction, date):
        return raw("departures_arn.json")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    # invalid 'ZZZ' -> reprompt -> 'ARN' -> choose 2 -> q -> q
    await menu.main_async(
        inputs=_fake_input(["ZZZ", "ARN", "2", "q", "q"]),
        now_iso="2026-06-17T00:00:00Z",
    )
    err = capsys.readouterr().err
    assert "ZZZ" in err or "Invalid" in err
