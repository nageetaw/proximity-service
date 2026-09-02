import os
from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

DB_PATH = os.getenv("SHOP_DB_PATH", "shops.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False is safe here because FastAPI/Starlette handles each
# request with a fresh Session (see get_session below).
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
