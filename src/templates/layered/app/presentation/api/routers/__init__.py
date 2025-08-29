"""Router aggregation."""

from .auth import router as auth  # noqa: F401

all_routers = [auth]
