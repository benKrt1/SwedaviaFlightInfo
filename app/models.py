from typing import Optional

from pydantic import BaseModel

_STATUS_SV_TO_EN = {
    "Avgått": "Departed",
    "Landat": "Landed",
    "Försenad": "Delayed",
    "Inställd": "Cancelled",
    "Boarding": "Boarding",
    "Gate stängd": "Gate closed",
    "Enligt tidtabell": "On time",
}


def translate_status(swedish: Optional[str]) -> Optional[str]:
    """Translate a Swedish Swedavia status to English, or pass it through."""
    if swedish is None:
        return None
    return _STATUS_SV_TO_EN.get(swedish, swedish)


class BaggageInfo(BaseModel):
    belt: Optional[str] = None
    firstBag: Optional[str] = None
    lastBag: Optional[str] = None


class Flight(BaseModel):
    flightNumber: Optional[str] = None
    airline: Optional[str] = None
    direction: str
    airport: str
    otherAirport: Optional[str] = None
    scheduledTime: Optional[str] = None
    estimatedTime: Optional[str] = None
    status: Optional[str] = None
    gate: Optional[str] = None
    terminal: Optional[str] = None
    baggage: Optional[BaggageInfo] = None


def _time(raw: dict, key: str) -> dict:
    return raw.get(key) or {}


def flight_from_raw(raw: dict, direction: str, airport: str) -> Flight:
    """Map one raw Swedavia flight dict into our clean Flight model."""
    loc = raw.get("locationAndStatus") or {}
    leg = raw.get("flightLegIdentifier") or {}
    airline = (raw.get("airlineOperator") or {}).get("name")

    if direction == "departure":
        times = _time(raw, "departureTime")
        other = leg.get("arrivalAirportIata")
    else:
        times = _time(raw, "arrivalTime")
        other = leg.get("departureAirportIata")

    # Swedavia already supplies an English status; fall back to translating the
    # Swedish one if the English field is missing.
    status = loc.get("flightLegStatusEnglish") or translate_status(
        loc.get("flightLegStatusSwedish")
    )

    baggage = None
    if direction == "arrival":
        bag = raw.get("baggage") or {}
        if bag:
            baggage = BaggageInfo(
                belt=bag.get("baggageClaimUnit"),
                firstBag=bag.get("firstBagUtc"),
                lastBag=bag.get("lastBagUtc"),
            )

    return Flight(
        flightNumber=raw.get("flightId"),
        airline=airline,
        direction=direction,
        airport=airport,
        otherAirport=other,
        scheduledTime=times.get("scheduledUtc"),
        estimatedTime=times.get("estimatedUtc"),
        status=status,
        gate=loc.get("gate"),
        terminal=loc.get("terminal"),
        baggage=baggage,
    )
