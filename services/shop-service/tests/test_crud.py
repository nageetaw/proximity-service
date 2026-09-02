from sqlmodel import Session

from app.crud import bulk_upsert_shops, get_shops_by_geohash_prefixes, upsert_shop
from app.geohash_utils import cover, encode
from app.schemas import ShopIn

# Test center: an arbitrary point.
CENTER_LAT, CENTER_LNG = 12.9352, 77.6146


def _shop_at(name: str, lat: float, lng: float, place_id: str | None = None) -> ShopIn:
    return ShopIn(google_place_id=place_id, name=name, lat=lat, lng=lng)


def test_upsert_creates_then_updates_by_place_id(session: Session):
    shop_in = _shop_at("Test Cafe", CENTER_LAT, CENTER_LNG, place_id="place-1")
    shop, created = upsert_shop(session, shop_in)
    session.commit()
    assert created is True
    assert shop.geohash == encode(CENTER_LAT, CENTER_LNG)

    updated_in = _shop_at("Test Cafe (renamed)", CENTER_LAT, CENTER_LNG, place_id="place-1")
    shop2, created2 = upsert_shop(session, updated_in)
    session.commit()
    assert created2 is False
    assert shop2.id == shop.id
    assert shop2.name == "Test Cafe (renamed)"


def test_geohash_prefix_query_respects_radius(session: Session):
    # Place shops at increasing offsets from the center: ~0m, ~400m, ~5km away.
    near = _shop_at("Near Shop", CENTER_LAT, CENTER_LNG, place_id="near")
    mid = _shop_at("Mid Shop", CENTER_LAT + 0.0036, CENTER_LNG, place_id="mid")  # ~400m north
    far = _shop_at("Far Shop", CENTER_LAT + 0.045, CENTER_LNG, place_id="far")  # ~5km north

    created, updated = bulk_upsert_shops(session, [near, mid, far])
    assert (created, updated) == (3, 0)

    precision, prefixes = cover(CENTER_LAT, CENTER_LNG, radius_m=500)
    results = get_shops_by_geohash_prefixes(session, prefixes, precision)
    names = {shop.name for shop in results}

    assert "Near Shop" in names
    assert "Mid Shop" in names
    assert "Far Shop" not in names
