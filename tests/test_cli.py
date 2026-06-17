import json
from pathlib import Path

import pytest

from app import cli, service
from app.cache import TTLCache
from app.models import BaggageInfo, Flight

FIX = Path(__file__).parent / "fixtures"


def raw(name):
    return json.loads((FIX / name).read_text())["flights"]


@pytest.fixture(autouse=True)
def reset_cache():
    service._cache = TTLCache(ttl_seconds=60)
    yield


# --- rendering helpers ---

def test_fmt_time_extracts_hh_mm():
    assert cli._fmt_time("2026-06-17T10:30:00Z") == "10:30"


def test_fmt_time_none_returns_dash():
    assert cli._fmt_time(None) == "-"


def test_render_table_departures_has_headers_and_row():
    flights = [
        Flight(
            flightNumber="SK1401", direction="departure", airport="ARN",
            otherAirport="CPH", scheduledTime="2026-06-17T10:30:00Z",
            status="Departed", gate="A12", terminal="5",
        )
    ]
    out = cli.render_table(flights, "departure")
    assert "Flight" in out and "To" in out and "Term" in out
    assert "SK1401" in out
    assert "CPH" in out
    assert "10:30" in out
    assert "Departed" in out


def test_render_table_arrivals_has_belt():
    flights = [
        Flight(
            flightNumber="SK1402", direction="arrival", airport="ARN",
            otherAirport="CPH", scheduledTime="2026-06-17T11:00:00Z",
            status="Landed", gate="E5",
            baggage=BaggageInfo(belt="3"),
        )
    ]
    out = cli.render_table(flights, "arrival")
    assert "From" in out and "Belt" in out
    assert "SK1402" in out
    assert "3" in out


def test_render_table_empty():
    assert cli.render_table([], "departure") == "No flights found."


# --- run() / parser ---

async def test_run_departures_prints_table(monkeypatch, capsys):
    async def fake_fetch(airport, direction, date):
        return raw("departures_arn.json")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    code = await cli.run(cli.build_parser().parse_args(["ARN", "departures"]))
    out = capsys.readouterr().out
    assert code == 0
    assert "SK1401" in out
    assert "Flight" in out


async def test_run_json_flag_outputs_valid_json(monkeypatch, capsys):
    async def fake_fetch(airport, direction, date):
        return raw("departures_arn.json")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    code = await cli.run(
        cli.build_parser().parse_args(["ARN", "departures", "--json"])
    )
    out = capsys.readouterr().out
    assert code == 0
    data = json.loads(out)
    assert data[0]["flightNumber"] == "SK1401"


async def test_run_search_found(monkeypatch, capsys):
    async def fake_fetch(airport, direction, date):
        return raw("departures_arn.json")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    code = await cli.run(
        cli.build_parser().parse_args(["ARN", "search", "SK1401"])
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "SK1401" in out


async def test_run_search_not_found_returns_1(monkeypatch, capsys):
    async def fake_fetch(airport, direction, date):
        return raw("departures_arn.json")

    monkeypatch.setattr(service, "fetch_flights", fake_fetch)

    code = await cli.run(
        cli.build_parser().parse_args(["ARN", "search", "ZZ9999"])
    )
    assert code == 1


async def test_run_invalid_airport_returns_2(capsys):
    code = await cli.run(cli.build_parser().parse_args(["XXX", "departures"]))
    err = capsys.readouterr().err
    assert code == 2
    assert "ARN" in err
