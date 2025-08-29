from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class Result(Generic[T]):
    success: bool
    value: Optional[T] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, value: T | None = None) -> "Result[T]":
        return cls(True, value=value)

    @classmethod
    def fail(cls, error: str) -> "Result[T]":
        return cls(False, error=error)
