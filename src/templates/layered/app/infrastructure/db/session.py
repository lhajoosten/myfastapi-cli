"""Optional SQLAlchemy session helpers.

Installed only when project is created with the extra dependency group `db`.
These are placeholders; real projects would add Base metadata, migrations etc.
"""
from __future__ import annotations

try:  # pragma: no cover - optional dependency path
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
except Exception:  # noqa: BLE001
    create_engine = None  # type: ignore
    sessionmaker = None  # type: ignore

ENGINE = None
SessionLocal = None  # type: ignore[assignment]


def init_engine(dsn: str) -> None:
    """Initialise global engine + session factory.

    Example: init_engine("sqlite:///./app.db")
    """
    global ENGINE, SessionLocal  # noqa: PLW0603
    if create_engine is None or sessionmaker is None:
        raise RuntimeError("SQLAlchemy not installed. Install project with [db] extras.")
    ENGINE = create_engine(dsn, future=True)
    SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)  # type: ignore[call-arg]
