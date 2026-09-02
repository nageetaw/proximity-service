import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from sqlmodel import Session

from app.crud import bulk_upsert_shops, get_shops_by_geohash_prefixes
from app.db import create_db_and_tables, get_session
from app.geohash_utils import MAX_PRECISION
from app.models import Shop
from app.schemas import ShopBulkIn, ShopBulkOut, ShopOut

INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "dev-internal-token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Shop Service", lifespan=lifespan)


def require_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    """Minimal shared-secret check for write endpoints. Not real auth — this
    service is expected to sit behind a private network / not be
    internet-facing; it's here only so a stray request can't overwrite data.
    """
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Internal-Token")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/shops", response_model=list[ShopOut])
def list_shops(
    geohash_prefixes: str = Query(..., description="Comma-separated geohash prefixes"),
    precision: int = Query(..., ge=1, le=MAX_PRECISION),
    session: Session = Depends(get_session),
) -> list[Shop]:
    prefixes = [p for p in geohash_prefixes.split(",") if p]
    return get_shops_by_geohash_prefixes(session, prefixes, precision)


@app.get("/shops/{shop_id}", response_model=ShopOut)
def get_shop(shop_id: int, session: Session = Depends(get_session)) -> Shop:
    shop = session.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


@app.post("/shops/bulk", response_model=ShopBulkOut, dependencies=[Depends(require_internal_token)])
def bulk_create_shops(
    payload: ShopBulkIn, session: Session = Depends(get_session)
) -> ShopBulkOut:
    created, updated = bulk_upsert_shops(session, payload.shops)
    return ShopBulkOut(created=created, updated=updated, total=created + updated)
