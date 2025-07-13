"""Custom exceptions for the ReportPortal AI Assistant."""


class ReportPortalAIError(Exception):
    """Base exception for all ReportPortal AI errors."""

    pass


class APIError(ReportPortalAIError):
    """Error related to API operations."""

    pass


class AuthenticationError(APIError):
    """Authentication failed."""

    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""

    pass


class SyncError(ReportPortalAIError):
    """Error during synchronization."""

    pass


class StorageError(ReportPortalAIError):
    """Error related to data storage operations."""

    pass


class EmbeddingError(ReportPortalAIError):
    """Error during embedding generation."""

    pass


class ConfigurationError(ReportPortalAIError):
    """Configuration related error."""

    pass
