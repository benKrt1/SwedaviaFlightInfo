import httpx

from app import config


class SwedaviaUnavailable(Exception):
    """Raised when the Swedavia API cannot be reached or returns an error."""


_DIRECTION_PATH = {"departure": "departures", "arrival": "arrivals"}


async def fetch_flights(airport: str, direction: str, date: str) -> list[dict]:
    """Call Swedavia FlightInfo v2 and return the raw list of flight dicts."""
    path_segment = _DIRECTION_PATH[direction]
    url = f"{config.SWEDAVIA_BASE_URL}/{airport}/{path_segment}/{date}"
    headers = {
        "Ocp-Apim-Subscription-Key": config.get_api_key(),
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        raise SwedaviaUnavailable(str(exc)) from exc

    if response.status_code >= 400:
        raise SwedaviaUnavailable(f"Swedavia returned {response.status_code}")

    return response.json().get("flights", [])
