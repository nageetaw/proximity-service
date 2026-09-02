from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Shop(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    google_place_id: str | None = Field(default=None, unique=True, index=True)

    name: str
    category: str | None = Field(default=None)
    address: str | None = Field(default=None)

    lat: float
    lng: float
    geohash: str = Field(index=True)

    rating: float | None = Field(default=None)

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
