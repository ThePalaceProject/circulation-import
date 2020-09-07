class BaseError(Exception):
    """Base class for all errors"""


class FatalError(BaseError):
    """Error raised when the application cannot continue working"""
