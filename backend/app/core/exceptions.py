class SentinelException(Exception):
    """Base exception for the application."""
    pass


class ValidationError(SentinelException):
    """Invalid input data."""
    pass


class NotFoundError(SentinelException):
    """Resource not found."""
    pass


class ProcessingError(SentinelException):
    """Video processing failed."""
    pass


class StorageError(SentinelException):
    """File storage operation failed."""
    pass