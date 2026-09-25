# Address Book API

A minimal FastAPI application for managing addresses with geographic
coordinates, backed by SQLite. Supports full CRUD plus a "find addresses
near a point" search.

## Features

- **Create / Read / Update / Delete** addresses
- **Validation** — latitude (-90 to 90) and longitude (-180 to 180) are
  range-checked by Pydantic; required text fields reject blank/whitespace
  values
- **SQLite persistence** via SQLAlchemy (auto-creates the DB file and table
  on first run)
- **Nearby search** — `GET /addresses/nearby` returns every address within
  a given radius (km) of a coordinate, sorted nearest-first, using the
  haversine formula (with an indexed bounding-box pre-filter so it doesn't
  scan the whole table)
- **Interactive API docs** at `/docs` (Swagger UI) and `/redoc`
- **Logging** of create/update/delete/search operations

## Project structure

```
address_book_api/
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI app + route handlers
│   ├── database.py      # SQLAlchemy engine/session setup
│   ├── models.py         # ORM model (Address table)
│   ├── schemas.py         # Pydantic request/response models + validation
│   ├── crud.py             # Database access functions
│   └── geo_utils.py         # Haversine distance + bounding-box helpers
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10+ (uses `tuple[float, float, float, float]` style type hints)

## Setup & run

Open a terminal in the project root (the folder containing this README)
and run:

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the API (auto-reloads on code changes)
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

Open **`http://127.0.0.1:8000/docs`** for the interactive Swagger UI,
where you can try every endpoint directly in the browser.

A SQLite file `address_book.db` is created automatically in the project
root the first time the app starts — no manual database setup needed.


This runs against an isolated in-memory SQLite database, so it never
touches `address_book.db`.

## API reference

| Method | Path                | Description                                   |
|--------|---------------------|------------------------------------------------|
| POST   | `/addresses`        | Create a new address                           |
| GET    | `/addresses`        | List addresses (paginated: `skip`, `limit`)    |
| GET    | `/addresses/{id}`   | Get one address by id                          |
| PUT    | `/addresses/{id}`   | Update one or more fields of an address        |
| DELETE | `/addresses/{id}`   | Delete an address                              |
| GET    | `/addresses/nearby` | Find addresses within `radius_km` of a point   |

### Example: create an address

```bash
curl -X POST http://127.0.0.1:8000/addresses \
  -H "Content-Type: application/json" \
  -d '{
        "street": "123 Rizal St",
        "city": "Tagum City",
        "state": "Davao del Norte",
        "postal_code": "8100",
        "country": "Philippines",
        "latitude": 7.4478,
        "longitude": 125.8072
      }'
```

### Example: find addresses within 50 km of a point

```bash
curl "http://127.0.0.1:8000/addresses/nearby?latitude=7.45&longitude=125.81&radius_km=50"
```

## Design notes

- **Layered structure**: routes (`main.py`) → data access (`crud.py`) →
  ORM models (`models.py`), with request/response validation
  (`schemas.py`) kept separate from the DB schema so the API contract can
  evolve independently of the table structure.
- **Nearby search performance**: SQLite has no built-in great-circle
  distance function, so an exact haversine calculation is done in Python.
  To avoid a full table scan on large datasets, a cheap bounding-box query
  (using the indexed `latitude`/`longitude` columns) first narrows the
  candidate set before the precise distance check and sort.
- **Partial updates**: `PUT /addresses/{id}` uses `exclude_unset=True` so
  callers only need to send the fields they want to change; any field that
  *is* sent is still fully validated (range/blank checks).
- Not in scope for this assignment (but noted for completeness): auth,
  rate limiting, and DB migrations (Alembic) — `Base.metadata.create_all`
  is used instead for simplicity.
