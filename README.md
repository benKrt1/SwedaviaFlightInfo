# Swedavia Flight Tracker (Backend)

A backend-only REST API that wraps Swedavia's public **FlightInfo v2** API. It
serves clean departures / arrivals / search / filter endpoints with caching, and
keeps the Swedavia subscription key secret. Swedish flight statuses are
translated to English.

## How it works

```
client  ->  this FastAPI app  ->  TTL cache  ->  Swedavia FlightInfo v2 API
                  |
                  +-- normalises raw data into our own clean Flight schema
```

The client only ever talks to our API. The Swedavia key lives in `.env` and is
never exposed or committed.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # then put your real key in .env
```

Get a free key at <https://apideveloper.swedavia.se/> (FlightInfo product).

## Run

```bash
.venv/bin/uvicorn app.main:app --reload
```

Interactive API docs: <http://127.0.0.1:8000/docs>

## Endpoints

| Method & path | Description |
|---|---|
| `GET /flights/{airport}/departures` | List departures (default: today). |
| `GET /flights/{airport}/arrivals` | List arrivals, including baggage belt. |
| `GET /flights/{airport}/search?flight=SK1401` | Find one flight by number. |
| `GET /health` | Health check. |

**Query parameters:**
- `date=YYYY-MM-DD` — defaults to today.
- `status=delayed|cancelled|ontime` — filter by status.
- `destination=CPH` — filter by the other airport's IATA code.

**Valid airports:** ARN, GOT, MMX, BMA, LLA, UME, VBY, KRN, RNB, VST, ORB, NYO.

Example:

```bash
curl "http://127.0.0.1:8000/flights/ARN/departures?status=delayed"
```

## Output schema

```json
{
  "flightNumber": "SK1401",
  "airline": "SAS",
  "direction": "departure",
  "airport": "ARN",
  "otherAirport": "CPH",
  "scheduledTime": "2026-06-17T10:30:00Z",
  "estimatedTime": "2026-06-17T10:45:00Z",
  "status": "Departed",
  "gate": "A12",
  "terminal": "5",
  "baggage": { "belt": "3", "firstBag": "11:20", "lastBag": "11:35" }
}
```

`baggage` is populated for arrivals and `null` for departures.

## Errors

| Situation | Response |
|---|---|
| Invalid airport code | `400` (lists valid codes) |
| Invalid date format | `400` |
| Flight not found (search) | `404` |
| Swedavia unreachable / error | `502` |
| Missing API key | app fails to start with a clear message |

## Tests

```bash
.venv/bin/pytest -v
```

Tests mock the Swedavia API — no key or network access needed.

## Project structure

```
app/
  config.py           # API key + base URL + valid airports
  cache.py            # in-memory TTL cache
  models.py           # Flight / BaggageInfo + status translation + mapping
  swedavia_client.py  # async httpx client for Swedavia
  service.py          # caching + filtering + search
  main.py             # FastAPI routes
tests/                # full pytest suite (mocked Swedavia)
```
