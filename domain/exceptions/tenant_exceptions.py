class TenantDomainException(Exception):
    """Base exception for tenatn domain errors"""
    pass

class TenantNotFoundError(TenantDomainException):
    """Raised when a tenant is not found"""

class TenantAlreadyExistsError(TenantDomainException):
    """Raised when tenant already exists"""
    pass
