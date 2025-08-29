"""Core domain / application exception types."""


class DomainError(Exception):
    """Base exception for domain errors."""


class NotFoundError(DomainError):
    """Raised when an entity is not found."""
