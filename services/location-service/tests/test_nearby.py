from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.schemas import ShopOut

CENTER_LAT, CENTER_LNG = 12.9352, 77.6146


def _shop(id_: int, lat: float, lng: float, name: str) -> ShopOut:
    now = datetime.now(timezone.utc)
    return ShopOut(
        id=id_,
        google_place_id=f"p{id_}",
        name=name,
        category="store",
        address="Somewhere",
        lat=lat,
        lng=lng,
        rating=4.5,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def client(monkeypatch):
    candidates = [
        _shop(1, CENTER_LAT, CENTER_LNG, "Near Shop"),  # ~0m
        _shop(2, CENTER_LAT + 0.0036, CENTER_LNG, "Mid Shop"),  # ~400m
        _shop(3, CENTER_LAT + 0.045, CENTER_LNG, "Far Shop"),  # ~5km — outside 500m radius
    ]

    async def fake_fetch(prefixes, precision):
        return candidates

    monkeypatch.setattr(main_module, "fetch_shops_by_geohash_prefixes", fake_fetch)
    return TestClient(main_module.app)


def test_nearby_filters_by_radius_and_sorts_by_distance(client: TestClient):
    resp = client.get("/nearby", params={"lat": CENTER_LAT, "lng": CENTER_LNG, "radius_m": 500})
    assert resp.status_code == 200
    body = resp.json()
    names = [s["name"] for s in body["shops"]]
    assert names == ["Near Shop", "Mid Shop"]  # sorted by distance, Far Shop excluded
    assert body["count"] == 2
    assert body["shops"][0]["distance_m"] < body["shops"][1]["distance_m"]


def test_nearby_rejects_invalid_radius(client: TestClient):
    resp = client.get("/nearby", params={"lat": CENTER_LAT, "lng": CENTER_LNG, "radius_m": 123})
    assert resp.status_code == 422


def test_nearby_defaults_radius_to_500(client: TestClient):
    resp = client.get("/nearby", params={"lat": CENTER_LAT, "lng": CENTER_LNG})
    assert resp.status_code == 200
    assert resp.json()["radius_m"] == 500
