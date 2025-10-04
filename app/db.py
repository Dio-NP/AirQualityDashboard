from __future__ import annotations
try:
    from sqlmodel import SQLModel, create_engine, Session
except Exception:  # pragma: no cover
    SQLModel = None  # type: ignore
    create_engine = None  # type: ignore
    Session = None  # type: ignore
from pathlib import Path
from config import settings

DB_PATH = Path(settings.data_dir) / "app.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False) if create_engine else None


def init_db() -> None:
    if SQLModel is None or engine is None:
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    if Session is None or engine is None:
        raise RuntimeError("Database not available: install sqlmodel")
    return Session(engine)
