# Proximity Shop Finder

Grant the browser location permission, and see real shops within a chosen
radius (500m default, or 1km / 2km / 5km) — powered by a geohash-based
proximity lookup across two small Python services.

See [`.claude/plans/`](.) or ask Claude for the original design doc; the
short version is below.

## Architecture

```
services/shop-service/       FastAPI, :8001 — owns the SQLite DB, dumb geohash-prefix queries
services/location-service/   FastAPI, :8000 — public-facing, geohash coverage + haversine filtering
frontend/                    Vite + React + Leaflet
```

- **shop-service** stores shops (`name`, `category`, `address`, `lat`, `lng`, `rating`,
  a `geohash` column) in SQLite and answers "give me shops whose geohash starts
  with any of these prefixes."
- **location-service** is stateless: given `lat, lng, radius_m`, it picks a
  geohash precision whose cell size covers the radius, asks shop-service for
  the center cell + its 8 neighbors, then does exact haversine filtering/sorting.
- **frontend** asks the browser for location permission, lets the user pick a
  radius, and renders results on a Leaflet/OpenStreetMap map + list.

## Prerequisites

- Python 3.11+ (this repo pins package versions tested against 3.12–3.14)
- Node.js 18+ and npm (for the frontend — not required to run the backend/tests)
- A Google Cloud project with **Places API (New)** enabled, if you want to seed
  real shop data (see [Seeding real data](#seeding-real-data-google-places-api))

## Setup

```bash
cp .env.example .env    # fill in GOOGLE_MAPS_API_KEY if you'll run ingestion

python3 -m venv .venv
./.venv/bin/pip install -r services/shop-service/requirements.txt
./.venv/bin/pip install -r services/location-service/requirements.txt
./.venv/bin/pip install pytest   # for running tests
```

## Running locally (without Docker)

```bash
# terminal 1
SHOP_DB_PATH=./data/shops.db INTERNAL_TOKEN=dev-internal-token \
  ./.venv/bin/uvicorn app.main:app --app-dir services/shop-service --port 8001 --reload

# terminal 2
SHOP_SERVICE_URL=http://localhost:8001 \
  ./.venv/bin/uvicorn app.main:app --app-dir services/location-service --port 8000 --reload

# terminal 3
cd frontend
npm install
npm run dev   # http://localhost:5173
```

## Running with Docker Compose

```bash
docker compose up --build
# shop-service:      http://localhost:8001
# location-service:  http://localhost:8000
```
Then run the frontend separately with `npm run dev` (see above) — it's not
containerized, since a fast local dev server is more useful while iterating.

## Seeding real data (Google Places API)

The app never calls Google live per user search — it only ever queries your
own SQLite DB. You seed that DB once (or occasionally) with a script that
grid-samples the Places API "Nearby Search" endpoint over an area you choose:

```bash
export GOOGLE_MAPS_API_KEY=...          # or put it in .env

./.venv/bin/python services/shop-service/ingestion/seed_from_google_places.py \
  --center 12.9352,77.6146 \
  --radius-km 2 \
  --grid-spacing-m 700 \
  --shop-service-url http://localhost:8001 \
  --internal-token dev-internal-token
```

Add `--dry-run` first to see how many shops would be found without writing
anything. The script only requests Pro-tier fields (name, address, location,
type, rating), which bills at **$32 per 1,000 calls** with a 5,000-call/month
free allotment — comfortably inside a modest Google Cloud credit balance for
seeding a city-sized area. See
[Google's pricing page](https://developers.google.com/maps/billing-and-pricing/pricing)
for current rates before running it against a new area.

## Tests

```bash
cd services/shop-service && ../../.venv/bin/python -m pytest -q
cd services/location-service && ../../.venv/bin/python -m pytest -q
```

## API

**location-service** (what the frontend calls):
```
GET /nearby?lat=&lng=&radius_m=500
→ { center, radius_m, count, shops: [{ ...shop, distance_m }] }
```
`radius_m` must be one of `500, 1000, 2000, 5000`.

**shop-service** (internal):
```
GET  /shops?geohash_prefixes=a,b,c&precision=7
GET  /shops/{id}
POST /shops/bulk        (requires X-Internal-Token header; used by ingestion)
```
