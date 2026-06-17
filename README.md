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

## Interactive menu (easiest)

Just run the program and pick from a menu — no arguments to remember:

```bash
.venv/bin/python main.py        # or: python3 main.py  (inside the venv)
```

```
Swedavia Flight Tracker — airport: ARN

  1) Baggage (belts)
  2) Departures
  3) Arrivals
  a) Change airport
  q) Quit
```

At the airport prompt press `Enter` for ARN, type a code (e.g. `GOT`), or type
`l` to pick from a numbered **list of all airports**.

Press `1`, `2`, or `3` to see the **next 10 flights from now** (sorted by time).
If the day is almost over, the list rolls into the **following day(s)** so you
still get a full page. Then press `Enter` for the next 10, `m` to go back to the
menu, or `q` to quit. Press `a` to switch airport. Times are UTC.

## Run from the terminal (CLI)

Prefer one-shot commands? Use the CLI instead of the menu:

```bash
.venv/bin/python -m app.cli ARN departures
.venv/bin/python -m app.cli ARN arrivals
.venv/bin/python -m app.cli ARN search SK1824
```

Output is a table:

```
Flight  From  Time   Status        Gate  Belt
SK1824  SKG   22:25  Landed 00:11  E5    6
SK1428  CPH   22:20  Landed 00:19  E6    5
```

Options:
- `--date YYYY-MM-DD` — defaults to today
- `--status delayed|cancelled|ontime` — filter by status
- `--destination CPH` — filter by the other airport's IATA code
- `--json` — print raw JSON instead of the table

Examples:

```bash
.venv/bin/python -m app.cli ARN departures --status delayed
.venv/bin/python -m app.cli ARN arrivals --destination CPH
.venv/bin/python -m app.cli ARN departures --json
```

Times are shown in UTC. Tip: make it shorter with an alias —
`alias flights=".venv/bin/python -m app.cli"` then `flights ARN departures`.

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
  main.py             # FastAPI routes (web API)
  cli.py              # terminal CLI (arguments, same service)
  menu.py             # interactive terminal menu
main.py               # launcher for the interactive menu
tests/                # full pytest suite (mocked Swedavia)
```
