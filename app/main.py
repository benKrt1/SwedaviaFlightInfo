from datetime import date as date_cls
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from app import config, service
from app.models import Flight
from app.swedavia_client import SwedaviaUnavailable

app = FastAPI(title="Swedavia Flight Tracker", version="1.0.0")


def _validate_airport(airport: str) -> str:
    code = airport.upper()
    if code not in config.VALID_AIRPORTS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid airport '{airport}'. "
                f"Valid codes: {', '.join(config.VALID_AIRPORTS)}"
            ),
        )
    return code


def _resolve_date(date: Optional[str]) -> str:
    if date is None:
        return date_cls.today().isoformat()
    try:
        date_cls.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")
    return date


async def _load(airport: str, direction: str, date: Optional[str]) -> list[Flight]:
    code = _validate_airport(airport)
    resolved = _resolve_date(date)
    try:
        return await service.get_flights(code, direction, resolved)
    except SwedaviaUnavailable:
        raise HTTPException(status_code=502, detail="Swedavia unavailable")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/flights/{airport}/departures", response_model=list[Flight])
async def departures(
    airport: str,
    date: Optional[str] = None,
    status: Optional[str] = Query(default=None),
    destination: Optional[str] = Query(default=None),
):
    flights = await _load(airport, "departure", date)
    return service.filter_flights(flights, status=status, destination=destination)


@app.get("/flights/{airport}/arrivals", response_model=list[Flight])
async def arrivals(
    airport: str,
    date: Optional[str] = None,
    status: Optional[str] = Query(default=None),
    destination: Optional[str] = Query(default=None),
):
    flights = await _load(airport, "arrival", date)
    return service.filter_flights(flights, status=status, destination=destination)


@app.get("/flights/{airport}/search", response_model=Flight)
async def search(airport: str, flight: str, date: Optional[str] = None):
    found = service.search_flight(await _load(airport, "departure", date), flight)
    if found is None:
        found = service.search_flight(await _load(airport, "arrival", date), flight)
    if found is None:
        raise HTTPException(status_code=404, detail="Flight not found")
    return found
