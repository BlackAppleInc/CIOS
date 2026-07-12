class DomainException(Exception):
    """Exception raised for domain rule violations."""
    pass

class LifecycleException(DomainException):
    """Exception raised when an invalid state transition is attempted."""
    pass
