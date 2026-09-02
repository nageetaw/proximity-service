from datetime import datetime

from pydantic import BaseModel


class ShopOut(BaseModel):
    id: int
    google_place_id: str | None = None
    name: str
    category: str | None = None
    address: str | None = None
    lat: float
    lng: float
    rating: float | None = None
    created_at: datetime
    updated_at: datetime


class NearbyShop(ShopOut):
    distance_m: float


class Center(BaseModel):
    lat: float
    lng: float


class NearbyResponse(BaseModel):
    center: Center
    radius_m: float
    count: int
    shops: list[NearbyShop]
