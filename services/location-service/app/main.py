from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.distance import haversine_m
from app.geohash_utils import cover
from app.schemas import Center, NearbyResponse, NearbyShop
from app.shop_client import fetch_shops_by_geohash_prefixes

ALLOWED_RADII_M = {500, 1000, 2000, 5000}

app = FastAPI(title="Location Service")

# The frontend (a separate origin during dev, e.g. localhost:5173) calls this
# service directly from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/nearby", response_model=NearbyResponse)
async def nearby(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_m: float = Query(500, description="500, 1000, 2000, or 5000 meters"),
) -> NearbyResponse:
    if radius_m not in ALLOWED_RADII_M:
        raise HTTPException(
            status_code=422,
            detail=f"radius_m must be one of {sorted(ALLOWED_RADII_M)}",
        )

    precision, prefixes = cover(lat, lng, radius_m)
    candidates = await fetch_shops_by_geohash_prefixes(prefixes, precision)

    shops: list[NearbyShop] = []
    for shop in candidates:
        distance_m = haversine_m(lat, lng, shop.lat, shop.lng)
        if distance_m <= radius_m:
            shops.append(NearbyShop(**shop.model_dump(), distance_m=distance_m))

    shops.sort(key=lambda s: s.distance_m)

    return NearbyResponse(
        center=Center(lat=lat, lng=lng),
        radius_m=radius_m,
        count=len(shops),
        shops=shops,
    )
