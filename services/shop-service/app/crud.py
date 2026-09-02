from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from app.geohash_utils import MAX_PRECISION, encode
from app.models import Shop
from app.schemas import ShopIn


def get_shops_by_geohash_prefixes(
    session: Session, prefixes: list[str], precision: int
) -> list[Shop]:
    """Return every shop whose geohash, truncated to `precision`, matches one
    of `prefixes`. `precision` must be <= MAX_PRECISION (the stored geohash
    length).
    """
    if not prefixes:
        return []

    statement = select(Shop).where(
        func.substr(Shop.geohash, 1, precision).in_(prefixes)
    )
    return list(session.exec(statement).all())


def upsert_shop(session: Session, shop_in: ShopIn) -> tuple[Shop, bool]:
    """Insert or update a shop (matched by google_place_id when present).
    Returns (shop, created).
    """
    existing: Shop | None = None
    if shop_in.google_place_id:
        existing = session.exec(
            select(Shop).where(Shop.google_place_id == shop_in.google_place_id)
        ).first()

    geohash = encode(shop_in.lat, shop_in.lng, MAX_PRECISION)
    now = datetime.now(timezone.utc)

    if existing:
        existing.name = shop_in.name
        existing.category = shop_in.category
        existing.address = shop_in.address
        existing.lat = shop_in.lat
        existing.lng = shop_in.lng
        existing.geohash = geohash
        existing.rating = shop_in.rating
        existing.updated_at = now
        session.add(existing)
        return existing, False

    shop = Shop(
        google_place_id=shop_in.google_place_id,
        name=shop_in.name,
        category=shop_in.category,
        address=shop_in.address,
        lat=shop_in.lat,
        lng=shop_in.lng,
        geohash=geohash,
        rating=shop_in.rating,
        created_at=now,
        updated_at=now,
    )
    session.add(shop)
    return shop, True


def bulk_upsert_shops(session: Session, shops_in: list[ShopIn]) -> tuple[int, int]:
    created = 0
    updated = 0
    for shop_in in shops_in:
        _, was_created = upsert_shop(session, shop_in)
        created += int(was_created)
        updated += int(not was_created)
    session.commit()
    return created, updated
