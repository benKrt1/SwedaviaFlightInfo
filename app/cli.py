"""Command-line interface for the Swedavia Flight Tracker.

Runs straight from the terminal, no web server needed:

    python -m app.cli ARN departures
    python -m app.cli ARN arrivals --status delayed
    python -m app.cli ARN search SK1824
"""

import argparse
import asyncio
import json
import sys
from datetime import date as date_cls
from typing import Optional

from app import config, service
from app.models import Flight
from app.swedavia_client import SwedaviaUnavailable


def _fmt_time(iso: Optional[str]) -> str:
    """Turn '2026-06-17T10:30:00Z' into '10:30' (times are UTC)."""
    if not iso or "T" not in iso:
        return "-"
    return iso.split("T", 1)[1][:5]


def _row(flight: Flight, direction: str) -> list[str]:
    if direction == "departure":
        last = flight.terminal or "-"
    else:
        last = (flight.baggage.belt if flight.baggage else None) or "-"
    return [
        flight.flightNumber or "-",
        flight.otherAirport or "-",
        _fmt_time(flight.scheduledTime),
        flight.status or "-",
        flight.gate or "-",
        last,
    ]


def render_table(flights: list[Flight], direction: str) -> str:
    """Render a list of flights as an aligned text table."""
    if not flights:
        return "No flights found."

    place = "To" if direction == "departure" else "From"
    last_header = "Term" if direction == "departure" else "Belt"
    headers = ["Flight", place, "Time", "Status", "Gate", last_header]

    rows = [_row(f, direction) for f in flights]
    widths = [
        max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(len(headers))
    ]

    def line(cols: list[str]) -> str:
        return "  ".join(col.ljust(widths[i]) for i, col in enumerate(cols)).rstrip()

    return "\n".join([line(headers)] + [line(r) for r in rows])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flights",
        description="Swedavia flight tracker — see departures and arrivals.",
    )
    parser.add_argument("airport", help="airport IATA code, e.g. ARN")
    parser.add_argument(
        "action",
        choices=["departures", "arrivals", "search"],
        help="what to show",
    )
    parser.add_argument(
        "flight", nargs="?", help="flight number (only for 'search'), e.g. SK1824"
    )
    parser.add_argument("--date", help="date as YYYY-MM-DD (default: today)")
    parser.add_argument(
        "--status", choices=["delayed", "cancelled", "ontime"], help="filter by status"
    )
    parser.add_argument("--destination", help="filter by the other airport's IATA code")
    parser.add_argument(
        "--json", action="store_true", help="print raw JSON instead of a table"
    )
    return parser


def _print_flights(flights: list[Flight], direction: str, as_json: bool) -> None:
    if as_json:
        print(json.dumps([f.model_dump() for f in flights], ensure_ascii=False, indent=2))
    else:
        print(render_table(flights, direction))


async def run(args: argparse.Namespace) -> int:
    airport = args.airport.upper()
    if airport not in config.VALID_AIRPORTS:
        print(
            f"Invalid airport '{args.airport}'. "
            f"Valid codes: {', '.join(config.VALID_AIRPORTS)}",
            file=sys.stderr,
        )
        return 2

    date = args.date or date_cls.today().isoformat()
    if args.date is not None:
        try:
            date_cls.fromisoformat(args.date)
        except ValueError:
            print("Invalid date. Use YYYY-MM-DD.", file=sys.stderr)
            return 2

    if args.action == "search":
        if not args.flight:
            print("Search needs a flight number, e.g. search SK1824", file=sys.stderr)
            return 2
        try:
            flights = await service.get_flights(airport, "departure", date)
            found = service.search_flight(flights, args.flight)
            if found is None:
                arrivals = await service.get_flights(airport, "arrival", date)
                found = service.search_flight(arrivals, args.flight)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        except SwedaviaUnavailable:
            print("Swedavia unavailable. Try again later.", file=sys.stderr)
            return 2
        if found is None:
            print(f"Flight '{args.flight}' not found.", file=sys.stderr)
            return 1
        _print_flights([found], found.direction, args.json)
        return 0

    direction = "departure" if args.action == "departures" else "arrival"
    try:
        flights = await service.get_flights(airport, direction, date)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except SwedaviaUnavailable:
        print("Swedavia unavailable. Try again later.", file=sys.stderr)
        return 2

    flights = service.filter_flights(
        flights, status=args.status, destination=args.destination
    )
    _print_flights(flights, direction, args.json)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    return asyncio.run(run(build_parser().parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
