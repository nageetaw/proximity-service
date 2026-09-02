"""Seed the Shop Service DB with real shops from the Google Places API (New).

Grid-samples Nearby Search calls over a bounding box around a center point so
we're not limited by the ~20-result cap of a single call, dedupes results by
Google's place id, and pushes them to Shop Service's POST /shops/bulk.

Uses only Pro-tier fields (displayName, formattedAddress, location, types,
rating) to keep every call at the $32/1000 Pro SKU price instead of the
pricier Enterprise SKU (which reviews/phone/website/hours fields trigger).

This is a manual, one-off (or occasionally re-run) script — it is NOT called
per user search, so live app usage costs $0 in Places API calls.

Usage:
    export GOOGLE_MAPS_API_KEY=...          # or put it in .env
    python ingestion/seed_from_google_places.py \
        --center 12.9352,77.6146 \
        --radius-km 2 \
        --grid-spacing-m 700 \
        --shop-service-url http://localhost:8001 \
        --internal-token dev-internal-token
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import time

import requests
from dotenv import load_dotenv

PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"

# Pro-tier field mask only — keeps every call at the $32/1000 Pro SKU price.
FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.types",
        "places.rating",
    ]
)

# A broad, generic "shop" set. Narrow this to your use case if you want fewer,
# more targeted categories (see https://developers.google.com/maps/documentation/places/web-service/place-types).
DEFAULT_INCLUDED_TYPES = [
    "store",
    "grocery_store",
    "supermarket",
    "convenience_store",
    "clothing_store",
    "shoe_store",
    "electronics_store",
    "book_store",
    "pharmacy",
    "bakery",
    "restaurant",
    "cafe",
]

EARTH_RADIUS_M = 6_371_000


def meters_to_lat_deg(m: float) -> float:
    return m / 111_320.0


def meters_to_lon_deg(m: float, at_lat: float) -> float:
    return m / (111_320.0 * math.cos(math.radians(at_lat)))


def build_grid(
    center_lat: float, center_lng: float, radius_km: float, grid_spacing_m: float
) -> list[tuple[float, float]]:
    """Build a square grid of sample points covering a circle of radius_km
    around (center_lat, center_lng), spaced grid_spacing_m apart.
    """
    radius_m = radius_km * 1000
    steps = max(1, math.ceil(radius_m / grid_spacing_m))
    points: list[tuple[float, float]] = []
    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            dx_m = i * grid_spacing_m
            dy_m = j * grid_spacing_m
            if math.hypot(dx_m, dy_m) > radius_m:
                continue
            lat = center_lat + meters_to_lat_deg(dy_m)
            lng = center_lng + meters_to_lon_deg(dx_m, center_lat)
            points.append((lat, lng))
    return points


def search_nearby(
    api_key: str, lat: float, lng: float, radius_m: float, included_types: list[str]
) -> list[dict]:
    body = {
        "includedTypes": included_types,
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_m,
            }
        },
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    resp = requests.post(PLACES_NEARBY_URL, json=body, headers=headers, timeout=15)
    if resp.status_code != 200:
        print(f"  ! Places API error {resp.status_code}: {resp.text[:300]}", file=sys.stderr)
        return []
    return resp.json().get("places", [])


def place_to_shop_in(place: dict) -> dict | None:
    location = place.get("location")
    if not location:
        return None
    return {
        "google_place_id": place.get("id"),
        "name": place.get("displayName", {}).get("text", "Unknown"),
        "category": (place.get("types") or [None])[0],
        "address": place.get("formattedAddress"),
        "lat": location["latitude"],
        "lng": location["longitude"],
        "rating": place.get("rating"),
    }


def push_to_shop_service(
    shop_service_url: str, internal_token: str, shops: list[dict]
) -> None:
    if not shops:
        return
    resp = requests.post(
        f"{shop_service_url}/shops/bulk",
        json={"shops": shops},
        headers={"X-Internal-Token": internal_token},
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    print(f"  -> upserted batch: {result}")


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--center", required=True, help="lat,lng of the area center")
    parser.add_argument("--radius-km", type=float, required=True, help="radius of the area to cover")
    parser.add_argument(
        "--grid-spacing-m",
        type=float,
        default=700,
        help="distance between grid sample points (smaller = more calls, denser coverage)",
    )
    parser.add_argument(
        "--per-call-radius-m",
        type=float,
        default=500,
        help="Nearby Search radius per grid point (keep <= grid-spacing-m so cells overlap slightly)",
    )
    parser.add_argument(
        "--included-types",
        nargs="*",
        default=DEFAULT_INCLUDED_TYPES,
        help="Google Places 'included type' values to search for",
    )
    parser.add_argument("--shop-service-url", default=os.getenv("SHOP_SERVICE_URL", "http://localhost:8001"))
    parser.add_argument("--internal-token", default=os.getenv("INTERNAL_TOKEN", "dev-internal-token"))
    parser.add_argument("--dry-run", action="store_true", help="fetch and print counts, don't write to DB")
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        sys.exit("GOOGLE_MAPS_API_KEY is not set (env var or .env file)")

    center_lat, center_lng = (float(x) for x in args.center.split(","))
    grid = build_grid(center_lat, center_lng, args.radius_km, args.grid_spacing_m)
    print(f"Grid: {len(grid)} sample points over ~{args.radius_km}km radius "
          f"(spacing {args.grid_spacing_m}m) -> up to {len(grid)} Places API calls")

    seen_place_ids: set[str] = set()
    all_shops: list[dict] = []

    for idx, (lat, lng) in enumerate(grid, start=1):
        places = search_nearby(api_key, lat, lng, args.per_call_radius_m, args.included_types)
        new_count = 0
        for place in places:
            place_id = place.get("id")
            if not place_id or place_id in seen_place_ids:
                continue
            seen_place_ids.add(place_id)
            shop = place_to_shop_in(place)
            if shop:
                all_shops.append(shop)
                new_count += 1
        print(f"[{idx}/{len(grid)}] ({lat:.5f},{lng:.5f}) -> {len(places)} results, {new_count} new")
        time.sleep(0.05)  # gentle pacing

    print(f"\nTotal unique shops found: {len(all_shops)}")

    if args.dry_run:
        print("--dry-run set, not writing to shop-service")
        return

    batch_size = 200
    for i in range(0, len(all_shops), batch_size):
        batch = all_shops[i : i + batch_size]
        print(f"Pushing shops {i}..{i + len(batch)} to {args.shop_service_url}")
        push_to_shop_service(args.shop_service_url, args.internal_token, batch)

    print("Done.")


if __name__ == "__main__":
    main()
