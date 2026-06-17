"""Interactive terminal menu for the Swedavia Flight Tracker.

Launch it from the repo root:

    python3 main.py        # inside the venv
    .venv/bin/python main.py
"""

import asyncio
import sys
from datetime import datetime, timezone
from typing import Callable

from app import cli, config, service
from app.models import Flight
from app.swedavia_client import SwedaviaUnavailable

PAGE = 10


# --- pure helpers -----------------------------------------------------------

def sort_by_time(flights: list[Flight]) -> list[Flight]:
    """Sort flights by scheduled time ascending; flights without a time go last."""
    return sorted(flights, key=lambda f: (f.scheduledTime is None, f.scheduledTime or ""))


def upcoming_from(flights: list[Flight], now_iso: str) -> list[Flight]:
    """Keep flights scheduled at or after now_iso, sorted by time."""
    future = [
        f for f in flights if f.scheduledTime and f.scheduledTime >= now_iso
    ]
    return sort_by_time(future)


def render_baggage(flights: list[Flight]) -> str:
    """Render arrivals focused on baggage: Flight | From | Belt | First | Last."""
    if not flights:
        return "No flights found."

    headers = ["Flight", "From", "Belt", "First", "Last"]
    rows = []
    for f in flights:
        bag = f.baggage
        rows.append([
            f.flightNumber or "-",
            f.otherAirport or "-",
            (bag.belt if bag else None) or "-",
            cli._fmt_time(bag.firstBag if bag else None),
            cli._fmt_time(bag.lastBag if bag else None),
        ])

    widths = [
        max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(len(headers))
    ]

    def line(cols):
        return "  ".join(c.ljust(widths[i]) for i, c in enumerate(cols)).rstrip()

    return "\n".join([line(headers)] + [line(r) for r in rows])


# --- interactive flow -------------------------------------------------------

_MENU = """
Swedavia Flight Tracker — airport: {airport}

  1) Αποσκευές (baggage / belts)
  2) Αναχωρήσεις (departures)
  3) Αφίξεις (arrivals)
  a) Άλλο αεροδρόμιο
  q) Έξοδος
"""


async def _show(
    airport: str,
    direction: str,
    render: Callable[[list[Flight]], str],
    now_iso: str,
    inputs: Callable[[str], str],
    page: int = PAGE,
) -> str:
    """Fetch flights and page through the upcoming ones. Returns 'menu' or 'quit'."""
    try:
        flights = await service.get_flights(airport, direction, now_iso[:10])
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return "menu"
    except SwedaviaUnavailable:
        print("Swedavia unavailable. Try again later.", file=sys.stderr)
        return "menu"

    flights = upcoming_from(flights, now_iso)
    if not flights:
        print("No upcoming flights found.")
        return "menu"

    offset = 0
    while offset < len(flights):
        chunk = flights[offset:offset + page]
        print()
        print(render(chunk))
        offset += page
        remaining = len(flights) - offset
        if remaining <= 0:
            print("\n(τέλος λίστας)")
            break
        print(f"\n[Enter] επόμενες {min(page, remaining)}   ·   [m] μενού   ·   [q] έξοδος")
        choice = inputs("> ").strip().lower()
        if choice == "q":
            return "quit"
        if choice == "m":
            return "menu"
    return "menu"


def _ask_airport(inputs: Callable[[str], str]) -> str | None:
    """Prompt for an airport code (Enter = ARN). Returns code, or None to quit."""
    while True:
        raw = inputs("Αεροδρόμιο (Enter = ARN, q = έξοδος): ").strip()
        if raw.lower() == "q":
            return None
        code = (raw or "ARN").upper()
        if code in config.VALID_AIRPORTS:
            return code
        print(
            f"Άκυρο '{raw}'. Έγκυρα: {', '.join(config.VALID_AIRPORTS)}",
            file=sys.stderr,
        )


async def main_async(inputs: Callable[[str], str] = input, now_iso: str | None = None) -> int:
    if now_iso is None:
        now_iso = datetime.now(timezone.utc).isoformat()

    airport = _ask_airport(inputs)
    if airport is None:
        return 0

    while True:
        print(_MENU.format(airport=airport))
        choice = inputs("Διάλεξε: ").strip().lower()

        if choice == "q":
            return 0
        if choice == "a":
            picked = _ask_airport(inputs)
            if picked is None:
                return 0
            airport = picked
            continue
        if choice == "1":
            result = await _show(airport, "arrival", render_baggage, now_iso, inputs)
        elif choice == "2":
            result = await _show(
                airport, "departure",
                lambda fl: cli.render_table(fl, "departure"), now_iso, inputs,
            )
        elif choice == "3":
            result = await _show(
                airport, "arrival",
                lambda fl: cli.render_table(fl, "arrival"), now_iso, inputs,
            )
        else:
            print("Διάλεξε 1, 2, 3, a ή q.", file=sys.stderr)
            continue

        if result == "quit":
            return 0


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
