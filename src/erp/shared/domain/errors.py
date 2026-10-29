class DomainError(Exception):
    """Base exception for domain errors."""


class PermissionDenied(DomainError):
    """Raised when a user lacks permission for an action."""


class NotFound(DomainError):
    """Raised when an entity is not found."""


class ValidationError(DomainError):
    """Raised when domain validation fails."""
