import os

import httpx

from app.schemas import ShopOut

SHOP_SERVICE_URL = os.getenv("SHOP_SERVICE_URL", "http://localhost:8001")


async def fetch_shops_by_geohash_prefixes(
    prefixes: list[str], precision: int
) -> list[ShopOut]:
    async with httpx.AsyncClient(base_url=SHOP_SERVICE_URL, timeout=10.0) as client:
        resp = await client.get(
            "/shops",
            params={"geohash_prefixes": ",".join(prefixes), "precision": precision},
        )
        resp.raise_for_status()
        return [ShopOut(**item) for item in resp.json()]
