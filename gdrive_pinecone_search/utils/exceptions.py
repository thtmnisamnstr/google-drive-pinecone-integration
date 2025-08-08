"""Custom exceptions for the Google Drive to Pinecone CLI."""


class GDriveSearchError(Exception):
    """Base exception for all GDrive Search errors."""
    pass


class AuthenticationError(GDriveSearchError):
    """Raised when authentication fails."""
    pass


class APIRateLimitError(GDriveSearchError):
    """Raised when API rate limits are exceeded."""
    pass


class IndexNotFoundError(GDriveSearchError):
    """Raised when a Pinecone index is not found."""
    pass


class IncompatibleIndexError(GDriveSearchError):
    """Raised when an index is incompatible with the current configuration."""
    pass


class ConfigurationError(GDriveSearchError):
    """Raised when there's a configuration issue."""
    pass


class DocumentProcessingError(GDriveSearchError):
    """Raised when document processing fails."""
    pass


class ConnectionError(GDriveSearchError):
    """Raised when connection to external services fails."""
    pass 