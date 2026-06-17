from typing import Optional

from app.cache import TTLCache
from app.models import Flight, flight_from_raw
from app.swedavia_client import fetch_flights

_cache = TTLCache(ttl_seconds=60)

_STATUS_FILTERS = {
    "delayed": {"Delayed"},
    "cancelled": {"Cancelled"},
    "ontime": {"On time"},
}


async def get_flights(airport: str, direction: str, date: str) -> list[Flight]:
    """Return mapped Flight models, using the cache when still fresh."""
    key = f"{airport}:{direction}:{date}"
    cached = _cache.get(key)
    if cached is not None:
        return cached

    raw_list = await fetch_flights(airport, direction, date)
    flights = [flight_from_raw(raw, direction, airport) for raw in raw_list]
    _cache.set(key, flights)
    return flights


def filter_flights(
    flights: list[Flight],
    status: Optional[str] = None,
    destination: Optional[str] = None,
) -> list[Flight]:
    result = flights
    if status:
        wanted = _STATUS_FILTERS.get(status.lower())
        if wanted is not None:
            result = [f for f in result if f.status in wanted]
    if destination:
        d = destination.lower()
        result = [f for f in result if (f.otherAirport or "").lower() == d]
    return result


def search_flight(flights: list[Flight], flight_number: str) -> Optional[Flight]:
    target = flight_number.lower()
    for f in flights:
        if (f.flightNumber or "").lower() == target:
            return f
    return None
