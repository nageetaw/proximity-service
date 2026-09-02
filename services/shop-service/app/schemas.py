from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShopIn(BaseModel):
    """A shop as submitted by the ingestion script (geohash computed server-side)."""

    google_place_id: str | None = None
    name: str
    category: str | None = None
    address: str | None = None
    lat: float
    lng: float
    rating: float | None = None


class ShopBulkIn(BaseModel):
    shops: list[ShopIn]


class ShopOut(BaseModel):
    id: int
    google_place_id: str | None
    name: str
    category: str | None
    address: str | None
    lat: float
    lng: float
    rating: float | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShopBulkOut(BaseModel):
    created: int
    updated: int
    total: int
