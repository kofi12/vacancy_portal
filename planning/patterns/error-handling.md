# 🚨 Error Handling Pattern

## Overview

Error handling patterns ensure consistent, informative, and secure error responses across the application while maintaining Clean Architecture principles.

## Domain Exception Hierarchy

### Base Exception Classes

```python
# domain/exceptions/base_exceptions.py
class DomainException(Exception):
    """Base class for all domain exceptions"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class BusinessRuleViolation(DomainException):
    """Raised when a business rule is violated"""
    pass

class EntityNotFound(DomainException):
    """Raised when an entity is not found"""
    pass

class EntityAlreadyExists(DomainException):
    """Raised when attempting to create an entity that already exists"""
    pass

class ValidationError(DomainException):
    """Raised when validation fails"""
    pass
```

### Specific Domain Exceptions

```python
# domain/exceptions/tenant_exceptions.py
class TenantDomainException(DomainException):
    """Base class for tenant-related exceptions"""
    pass

class TenantNotFoundError(TenantDomainException):
    """Raised when tenant is not found"""
    
    def __init__(self, tenant_id: int):
        super().__init__(
            message=f"Tenant with ID {tenant_id} not found",
            error_code="TENANT_NOT_FOUND",
            details={"tenant_id": tenant_id}
        )
        self.tenant_id = tenant_id

class TenantAlreadyExistsError(TenantDomainException):
    """Raised when tenant already exists"""
    
    def __init__(self, tenant_name: str, organization_id: int):
        super().__init__(
            message=f"Tenant '{tenant_name}' already exists in organization {organization_id}",
            error_code="TENANT_ALREADY_EXISTS",
            details={
                "tenant_name": tenant_name,
                "organization_id": organization_id
            }
        )
        self.tenant_name = tenant_name
        self.organization_id = organization_id

class TenantAdmissionError(TenantDomainException):
    """Raised when tenant admission fails"""
    pass

class TenantDischargeError(TenantDomainException):
    """Raised when tenant discharge fails"""
    pass
```

## Application Layer Error Handling

### Use Case Error Handling

```python
# application/use_cases/create_tenant_use_case.py
class CreateTenantUseCase:
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self, request: CreateTenantRequest) -> TenantResponse:
        """Execute tenant creation with error handling"""
        try:
            # Validate request
            self._validate_request(request)
            
            # Convert to domain entity
            tenant = TenantEntity.create_tenant(
                name=request.name,
                organization_id=request.organization_id,
                is_waitlist=request.is_waitlist
            )
            
            # Execute business logic
            created_tenant = await self._tenant_service.create_tenant(tenant)
            
            # Convert to response
            return TenantResponse.from_entity(created_tenant)
            
        except TenantAlreadyExistsError:
            # Re-raise domain exceptions as-is
            raise
        except Exception as e:
            # Wrap unexpected errors
            logger.error(f"Unexpected error in CreateTenantUseCase: {str(e)}")
            raise ApplicationError(
                message="Failed to create tenant",
                original_error=e
            ) from e
    
    def _validate_request(self, request: CreateTenantRequest):
        """Validate request data"""
        if not request.name or not request.name.strip():
            raise ValidationError("Tenant name is required")
        
        if request.organization_id <= 0:
            raise ValidationError("Valid organization ID is required")
```

### Application-Level Exceptions

```python
# application/exceptions/application_exceptions.py
class ApplicationException(Exception):
    """Base class for application layer exceptions"""
    
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.message = message
        self.original_error = original_error

class ApplicationError(ApplicationException):
    """Generic application error"""
    pass

class ValidationError(ApplicationException):
    """Request validation error"""
    pass

class AuthorizationError(ApplicationException):
    """Authorization error"""
    pass

class AuthenticationError(ApplicationException):
    """Authentication error"""
    pass
```

## Infrastructure Layer Error Handling

### Repository Error Handling

```python
# infrastructure/database/exceptions/repository_exceptions.py
class RepositoryException(Exception):
    """Base repository exception"""
    pass

class EntityNotFoundError(RepositoryException):
    """Entity not found in repository"""
    pass

class ConcurrencyError(RepositoryException):
    """Concurrent modification error"""
    pass

class ConnectionError(RepositoryException):
    """Database connection error"""
    pass

# infrastructure/database/repositories/sql_tenant_repository.py
class SQLTenantRepository(TenantRepository):
    async def get_by_id(self, id: int) -> Optional[TenantEntity]:
        """Get tenant by ID with error handling"""
        try:
            stmt = select(TenantModel).where(TenantModel.id == id)
            result = await self._session.execute(stmt)
            tenant_model = result.scalar_one_or_none()
            
            if not tenant_model:
                raise EntityNotFoundError(f"Tenant with ID {id} not found")
            
            return self._to_entity(tenant_model)
            
        except IntegrityError as e:
            logger.error(f"Database integrity error: {str(e)}")
            raise ConcurrencyError("Data was modified by another process") from e
        except OperationalError as e:
            logger.error(f"Database operational error: {str(e)}")
            raise ConnectionError("Database operation failed") from e
        except Exception as e:
            logger.error(f"Unexpected repository error: {str(e)}")
            raise RepositoryException(f"Failed to get tenant: {str(e)}") from e
```

### External Service Error Handling

```python
# infrastructure/external/exceptions/external_exceptions.py
class ExternalServiceException(Exception):
    """Base external service exception"""
    pass

class ServiceUnavailableError(ExternalServiceException):
    """External service is unavailable"""
    pass

class ServiceTimeoutError(ExternalServiceException):
    """External service timed out"""
    pass

class ServiceAuthenticationError(ExternalServiceException):
    """Authentication failed with external service"""
    pass

# infrastructure/external/email_service.py
class EmailService:
    async def send_admission_notification(self, tenant: TenantEntity) -> None:
        """Send admission notification with error handling"""
        try:
            # Attempt to send email
            await self._email_client.send(
                to=tenant.email,
                subject="Admission Confirmed",
                body=self._build_admission_email(tenant)
            )
            
        except TimeoutError as e:
            logger.warning(f"Email service timeout for tenant {tenant.id}")
            # Don't re-raise - email failure shouldn't break admission
            await self._queue_for_retry(tenant)
            
        except AuthenticationError as e:
            logger.error(f"Email service authentication failed: {str(e)}")
            raise ServiceAuthenticationError("Email service authentication failed") from e
            
        except Exception as e:
            logger.error(f"Unexpected email service error: {str(e)}")
            # Don't re-raise - email failure shouldn't break admission
            await self._log_failure(tenant, str(e))
```

## Presentation Layer Error Handling

### HTTP Exception Mapping

```python
# presentation/exceptions/http_exceptions.py
from fastapi import HTTPException, status
from domain.exceptions.tenant_exceptions import (
    TenantNotFoundError, TenantAlreadyExistsError, TenantAdmissionError
)
from domain.exceptions.user_exceptions import (
    UserNotFoundError, UserAlreadyExistsError
)
from application.exceptions.application_exceptions import (
    ValidationError, AuthorizationError, AuthenticationError
)

def map_domain_to_http_exception(error: Exception) -> HTTPException:
    """Map domain exceptions to HTTP exceptions"""
    
    # Tenant domain exceptions
    if isinstance(error, TenantNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": error.error_code,
                "message": error.message,
                "details": error.details
            }
        )
    
    elif isinstance(error, TenantAlreadyExistsError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": error.error_code,
                "message": error.message,
                "details": error.details
            }
        )
    
    elif isinstance(error, TenantAdmissionError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": error.error_code,
                "message": error.message,
                "details": error.details
            }
        )
    
    # User domain exceptions
    elif isinstance(error, UserNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": error.error_code,
                "message": error.message,
                "details": error.details
            }
        )
    
    # Application exceptions
    elif isinstance(error, ValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": error.message,
                "details": getattr(error, 'details', {})
            }
        )
    
    elif isinstance(error, AuthorizationError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "AUTHORIZATION_ERROR",
                "message": "Insufficient permissions",
                "details": {}
            }
        )
    
    elif isinstance(error, AuthenticationError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "AUTHENTICATION_ERROR",
                "message": "Authentication required",
                "details": {}
            }
        )
    
    # Default case
    else:
        logger.error(f"Unhandled exception: {type(error).__name__}: {str(error)}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        )
```

### Exception Handler Decorator

```python
# presentation/middleware/exception_handler.py
import logging
from functools import wraps
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def handle_exceptions(func):
    """Decorator to handle exceptions in controller methods"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Map domain/application exceptions to HTTP exceptions
            if hasattr(e, 'error_code'):  # Domain exception
                http_exception = map_domain_to_http_exception(e)
                raise http_exception
            elif isinstance(e, HTTPException):
                # Already an HTTP exception, re-raise
                raise
            else:
                # Unexpected exception
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred",
                        "details": {}
                    }
                )
    
    return wrapper
```

### Controller Error Handling

```python
# presentation/controllers/tenant_controller.py
@tenant_router.post("/tenants")
@handle_exceptions
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
) -> TenantResponse:
    """Create a new tenant"""
    return await use_case.execute(request)

@tenant_router.post("/tenants/{tenant_id}/admit")
@handle_exceptions
async def admit_tenant(
    tenant_id: int,
    request: AdmitTenantRequest,
    use_case: AdmitTenantUseCase = Depends(get_admit_tenant_use_case)
) -> TenantResponse:
    """Admit a tenant"""
    request.tenant_id = tenant_id  # Set path parameter
    return await use_case.execute(request)
```

## Error Logging and Monitoring

### Structured Logging Pattern

```python
# infrastructure/logging/error_logger.py
import logging
import json
from datetime import datetime
from typing import Dict, Any

class ErrorLogger:
    """Structured error logging"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
    
    def log_domain_error(self, error: DomainException, context: Dict[str, Any] = None):
        """Log domain errors with structured data"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "error_type": "DOMAIN_ERROR",
            "error_code": error.error_code,
            "message": error.message,
            "details": error.details,
            "context": context or {}
        }
        
        self._logger.error(json.dumps(log_data))
    
    def log_application_error(self, error: ApplicationException, context: Dict[str, Any] = None):
        """Log application errors"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR", 
            "error_type": "APPLICATION_ERROR",
            "message": error.message,
            "original_error": str(error.original_error) if error.original_error else None,
            "context": context or {}
        }
        
        self._logger.error(json.dumps(log_data))
    
    def log_infrastructure_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log infrastructure errors"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "error_type": "INFRASTRUCTURE_ERROR", 
            "error_class": error.__class__.__name__,
            "message": str(error),
            "context": context or {}
        }
        
        self._logger.error(json.dumps(log_data))
```

### Error Metrics and Monitoring

```python
# infrastructure/monitoring/error_monitor.py
from collections import defaultdict
import time
from typing import Dict, List

class ErrorMonitor:
    """Monitor error rates and patterns"""
    
    def __init__(self):
        self._error_counts = defaultdict(int)
        self._error_timestamps: Dict[str, List[float]] = defaultdict(list)
        self._window_size = 3600  # 1 hour window
    
    def record_error(self, error_type: str, error_code: str = None):
        """Record an error occurrence"""
        key = f"{error_type}:{error_code}" if error_code else error_type
        
        self._error_counts[key] += 1
        self._error_timestamps[key].append(time.time())
        
        # Clean old timestamps
        self._cleanup_old_timestamps(key)
    
    def get_error_rate(self, error_type: str, error_code: str = None, 
                      window_seconds: int = 3600) -> float:
        """Get error rate per hour for specific error"""
        key = f"{error_type}:{error_code}" if error_code else error_type
        
        if key not in self._error_timestamps:
            return 0.0
        
        # Count errors in time window
        cutoff = time.time() - window_seconds
        recent_errors = [t for t in self._error_timestamps[key] if t > cutoff]
        
        # Calculate rate per hour
        hours = window_seconds / 3600
        return len(recent_errors) / hours if hours > 0 else 0.0
    
    def get_all_error_rates(self, window_seconds: int = 3600) -> Dict[str, float]:
        """Get error rates for all error types"""
        rates = {}
        for error_type in self._error_counts.keys():
            rates[error_type] = self.get_error_rate(error_type, window_seconds=window_seconds)
        return rates
    
    def _cleanup_old_timestamps(self, key: str):
        """Remove timestamps outside the monitoring window"""
        cutoff = time.time() - self._window_size
        self._error_timestamps[key] = [
            t for t in self._error_timestamps[key] if t > cutoff
        ]
```

## Testing Error Scenarios

### Domain Exception Testing

```python
# tests/domain/test_tenant_entity.py
def test_tenant_creation_validation_error():
    """Test that tenant creation raises validation errors"""
    with pytest.raises(ValueError, match="Tenant name cannot be empty"):
        TenantEntity.create_tenant("", 1)

def test_tenant_admission_business_rule_error():
    """Test business rule violation in admission"""
    tenant = TenantEntity.create_tenant("Test", 1, is_waitlist=False)
    
    with pytest.raises(ValueError, match="Tenant cannot be admitted"):
        tenant.admit(datetime.utcnow())
```

### Repository Error Testing

```python
# tests/infrastructure/repositories/test_sql_tenant_repository.py
@pytest.mark.asyncio
async def test_get_by_id_not_found(repository, mock_session):
    """Test handling of not found errors"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    with pytest.raises(EntityNotFoundError, match="Tenant with ID 999 not found"):
        await repository.get_by_id(999)
```

### API Error Testing

```python
# tests/presentation/controllers/test_tenant_controller.py
def test_create_tenant_validation_error(client):
    """Test API validation error handling"""
    response = client.post(
        "/api/v2/tenants",
        json={"name": "", "organization_id": 1}  # Invalid: empty name
    )
    
    assert response.status_code == 422
    error = response.json()
    assert error["error_code"] == "VALIDATION_ERROR"
    assert "name" in str(error["details"])

def test_get_tenant_not_found(client):
    """Test API not found error handling"""
    response = client.get("/api/v2/tenants/999")
    
    assert response.status_code == 404
    error = response.json()
    assert error["error_code"] == "TENANT_NOT_FOUND"
    assert error["details"]["tenant_id"] == 999
```

## Error Recovery Patterns

### Retry Pattern

```python
# infrastructure/external/retry_handler.py
import asyncio
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class RetryHandler:
    """Handle retries for transient failures"""
    
    def __init__(self, max_attempts: int = 3, backoff_factor: float = 1.0):
        self._max_attempts = max_attempts
        self._backoff_factor = backoff_factor
    
    async def execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation with retry logic"""
        last_exception = None
        
        for attempt in range(self._max_attempts):
            try:
                return await operation(*args, **kwargs)
            except (ConnectionError, TimeoutError) as e:
                last_exception = e
                if attempt < self._max_attempts - 1:
                    wait_time = self._backoff_factor * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {self._max_attempts} attempts failed: {str(e)}")
                    raise
            except Exception as e:
                # Don't retry for non-transient errors
                logger.error(f"Non-retryable error: {str(e)}")
                raise
        
        raise last_exception
```

### Circuit Breaker Pattern

```python
# infrastructure/external/circuit_breaker.py
import time
import logging
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time = None
        self._state = CircuitState.CLOSED
    
    async def call(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation through circuit breaker"""
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker half-open, testing service")
            else:
                raise ServiceUnavailableError("Circuit breaker is OPEN")
        
        try:
            result = await operation(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self._last_failure_time is None:
            return False
        
        return time.time() - self._last_failure_time >= self._recovery_timeout
    
    def _on_success(self):
        """Handle successful operation"""
        if self._state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker reset to CLOSED")
            self._state = CircuitState.CLOSED
        
        self._failure_count = 0
    
    def _on_failure(self):
        """Handle failed operation"""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self._failure_threshold:
            logger.warning(f"Circuit breaker opened after {self._failure_count} failures")
            self._state = CircuitState.OPEN
```

This pattern ensures consistent, informative, and secure error handling across all layers while maintaining Clean Architecture principles.
