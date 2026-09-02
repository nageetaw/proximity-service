from fastapi.testclient import TestClient

CENTER_LAT, CENTER_LNG = 12.9352, 77.6146


def test_bulk_create_requires_internal_token(client: TestClient):
    resp = client.post("/shops/bulk", json={"shops": []})
    assert resp.status_code == 401


def test_bulk_create_and_list_by_geohash(client: TestClient, monkeypatch):
    payload = {
        "shops": [
            {"name": "Corner Store", "lat": CENTER_LAT, "lng": CENTER_LNG, "google_place_id": "p1"},
        ]
    }
    resp = client.post(
        "/shops/bulk", json=payload, headers={"X-Internal-Token": "dev-internal-token"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"created": 1, "updated": 0, "total": 1}

    from app.geohash_utils import cover

    precision, prefixes = cover(CENTER_LAT, CENTER_LNG, radius_m=500)
    resp = client.get(
        "/shops", params={"geohash_prefixes": ",".join(prefixes), "precision": precision}
    )
    assert resp.status_code == 200
    names = {shop["name"] for shop in resp.json()}
    assert "Corner Store" in names
