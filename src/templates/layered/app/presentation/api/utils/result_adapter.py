from __future__ import annotations

from fastapi import HTTPException
from app.application.common.models.result_model import Result  # type: ignore[import-not-found]

ERROR_STATUS_MAP = {
    "NOT_FOUND": 404,
    "VALIDATION_ERROR": 422,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
}


def unwrap_or_raise(result: Result, default_status: int = 400):  # type: ignore[type-arg]
    """Convert a Result into a value or raise HTTPException.

    Maps known error codes to HTTP status; falls back to default_status.
    """
    if result.success:
        return result.value
    status = ERROR_STATUS_MAP.get(result.error or "", default_status)
    raise HTTPException(status_code=status, detail=result.error or "error")


__all__ = ["unwrap_or_raise"]