# 🏗️ Domain Services Pattern

## Overview

Domain services contain business logic that doesn't naturally belong to a single entity but is still part of the domain layer.

## When to Use Domain Services

### ✅ Use Domain Services For

- **Multi-entity operations**: Logic involving multiple entities
- **Complex business rules**: Rules spanning entity boundaries
- **Domain calculations**: Business computations
- **External service coordination**: Orchestrating domain operations

### ❌ Don't Use Domain Services For

- **Simple entity operations**: Belongs in entity methods
- **Data access**: Belongs in repositories
- **HTTP concerns**: Belongs in controllers
- **Infrastructure logic**: Belongs in infrastructure services

## Service Patterns

### Basic Domain Service

```python
class TenantAdmissionService:
    """Domain service for tenant admission logic"""
    
    def __init__(self, tenant_repository: TenantRepository):
        self._tenant_repository = tenant_repository
    
    async def admit_tenant(self, tenant_id: int, admission_date: datetime) -> TenantEntity:
        """Business logic for admitting a tenant"""
        tenant = await self._tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")
        
        # Business rule: Check admission eligibility
        if not tenant.can_be_admitted():
            raise TenantAdmissionError("Tenant cannot be admitted")
        
        # Business rule: Validate admission date
        if admission_date < datetime.utcnow():
            raise TenantAdmissionError("Admission date cannot be in the past")
        
        # Apply business logic
        tenant.admit(admission_date)
        
        return await self._tenant_repository.update(tenant)
```

### Multi-Entity Service

```python
class OrganizationCapacityService:
    """Domain service managing organization capacity"""
    
    def __init__(self, 
                 org_repository: OrganizationRepository,
                 tenant_repository: TenantRepository):
        self._org_repository = org_repository
        self._tenant_repository = tenant_repository
    
    async def check_admission_capacity(self, org_id: int) -> bool:
        """Business rule: Check if organization can admit more tenants"""
        org = await self._org_repository.get_by_id(org_id)
        if not org:
            raise OrganizationNotFoundError(f"Organization {org_id} not found")
        
        current_tenants = await self._tenant_repository.get_by_organization(org_id)
        admitted_tenants = [t for t in current_tenants if t.is_currently_admitted()]
        
        return len(admitted_tenants) < org.max_capacity
    
    async def get_capacity_report(self, org_id: int) -> CapacityReport:
        """Generate capacity utilization report"""
        org = await self._org_repository.get_by_id(org_id)
        current_tenants = await self._tenant_repository.get_by_organization(org_id)
        
        total_tenants = len(current_tenants)
        admitted_tenants = len([t for t in current_tenants if t.is_currently_admitted()])
        waitlist_tenants = len([t for t in current_tenants if t.is_waitlist])
        
        return CapacityReport(
            organization_id=org_id,
            max_capacity=org.max_capacity,
            current_admitted=admitted_tenants,
            current_waitlist=waitlist_tenants,
            utilization_rate=admitted_tenants / org.max_capacity,
            available_spots=org.max_capacity - admitted_tenants
        )
```

### Calculation Service

```python
class TenantMetricsService:
    """Domain service for tenant-related calculations"""
    
    def __init__(self, tenant_repository: TenantRepository):
        self._tenant_repository = tenant_repository
    
    async def calculate_average_stay_duration(self, org_id: int) -> float:
        """Calculate average tenant stay duration in days"""
        tenants = await self._tenant_repository.get_by_organization(org_id)
        completed_stays = [
            tenant for tenant in tenants 
            if tenant.admission_date and tenant.discharge_date
        ]
        
        if not completed_stays:
            return 0.0
        
        total_days = sum(
            (tenant.discharge_date - tenant.admission_date).days
            for tenant in completed_stays
        )
        
        return total_days / len(completed_stays)
    
    async def predict_admission_probability(self, tenant: TenantEntity) -> float:
        """Business logic: Predict admission likelihood"""
        # Simplified prediction based on business rules
        score = 0.0
        
        # Factor 1: Waitlist position (earlier = higher chance)
        if tenant.created_at:
            days_waiting = (datetime.utcnow() - tenant.created_at).days
            if days_waiting > 30:
                score += 0.3
        
        # Factor 2: Organization capacity
        # (This would check current capacity vs max capacity)
        
        return min(score + 0.5, 1.0)  # Base 50% + factors
```

## Service Organization Patterns

### Service Interface Pattern

```python
# domain/services/interfaces/tenant_admission_service.py
class TenantAdmissionServiceInterface(ABC):
    """Interface for tenant admission operations"""
    
    @abstractmethod
    async def admit_tenant(self, tenant_id: int, admission_date: datetime) -> TenantEntity:
        pass
    
    @abstractmethod
    async def validate_admission_requirements(self, tenant_id: int) -> bool:
        pass

# domain/services/tenant_admission_service.py
class TenantAdmissionService(TenantAdmissionServiceInterface):
    """Concrete implementation"""
    # Implementation here
```

### Service Composition Pattern

```python
class ComprehensiveTenantService:
    """Service that composes multiple domain services"""
    
    def __init__(self,
                 admission_service: TenantAdmissionService,
                 metrics_service: TenantMetricsService,
                 capacity_service: OrganizationCapacityService):
        self._admission_service = admission_service
        self._metrics_service = metrics_service
        self._capacity_service = capacity_service
    
    async def process_tenant_admission_workflow(self, tenant_id: int, org_id: int):
        """Complete admission workflow using multiple services"""
        # Step 1: Check capacity
        has_capacity = await self._capacity_service.check_admission_capacity(org_id)
        if not has_capacity:
            raise OrganizationAtCapacityError()
        
        # Step 2: Validate admission requirements
        can_admit = await self._admission_service.validate_admission_requirements(tenant_id)
        if not can_admit:
            raise TenantNotEligibleError()
        
        # Step 3: Process admission
        admission_date = datetime.utcnow()
        admitted_tenant = await self._admission_service.admit_tenant(tenant_id, admission_date)
        
        # Step 4: Update metrics (async, doesn't block admission)
        # Could trigger background job here
        
        return admitted_tenant
```

## Testing Patterns

### Unit Testing Domain Services

```python
import pytest
from unittest.mock import AsyncMock
from domain.services.tenant_admission_service import TenantAdmissionService

@pytest.fixture
def mock_repository():
    return AsyncMock()

@pytest.fixture
def admission_service(mock_repository):
    return TenantAdmissionService(mock_repository)

@pytest.mark.asyncio
async def test_admit_tenant_success(admission_service, mock_repository):
    """Test successful tenant admission"""
    # Arrange
    tenant = TenantEntity(
        id=1, name="Test Tenant", is_waitlist=True,
        created_at=datetime.utcnow()
    )
    mock_repository.get_by_id.return_value = tenant
    
    admission_date = datetime.utcnow()
    
    # Act
    result = await admission_service.admit_tenant(1, admission_date)
    
    # Assert
    assert result.is_currently_admitted() == True
    assert result.admission_date == admission_date
    mock_repository.update.assert_called_once()

@pytest.mark.asyncio
async def test_admit_tenant_not_found(admission_service, mock_repository):
    """Test admission of non-existent tenant"""
    # Arrange
    mock_repository.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(TenantNotFoundError):
        await admission_service.admit_tenant(999, datetime.utcnow())
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_admission_workflow_integration(
    db_session,
    tenant_repository,
    admission_service,
    capacity_service
):
    """Test complete admission workflow"""
    # Arrange
    tenant = TenantEntity.create_tenant("Integration Test", 1, is_waitlist=True)
    created_tenant = await tenant_repository.create(tenant)
    
    # Act
    admitted_tenant = await admission_service.admit_tenant(
        created_tenant.id, datetime.utcnow()
    )
    
    # Assert
    assert admitted_tenant.is_currently_admitted() == True
    
    # Verify in database
    retrieved = await tenant_repository.get_by_id(created_tenant.id)
    assert retrieved.is_currently_admitted() == True
```

## Error Handling Patterns

### Domain Service Exceptions

```python
class TenantDomainException(Exception):
    """Base exception for tenant domain errors"""
    pass

class TenantAdmissionError(TenantDomainException):
    """Raised when tenant admission fails"""
    pass

class OrganizationCapacityError(TenantDomainException):
    """Raised when organization is at capacity"""
    pass

# Usage in service
async def admit_tenant(self, tenant_id: int, admission_date: datetime):
    """Admit tenant with comprehensive error handling"""
    try:
        tenant = await self._tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")
        
        if not tenant.can_be_admitted():
            raise TenantAdmissionError("Tenant not eligible for admission")
        
        # Check organization capacity
        has_capacity = await self._check_organization_capacity(tenant.organization_id)
        if not has_capacity:
            raise OrganizationCapacityError("Organization at maximum capacity")
        
        tenant.admit(admission_date)
        return await self._tenant_repository.update(tenant)
        
    except Exception as e:
        # Log error details
        logger.error(f"Failed to admit tenant {tenant_id}: {str(e)}")
        raise
```

## Performance Patterns

### Caching Pattern

```python
from functools import lru_cache
import asyncio

class CachedMetricsService:
    """Service with caching for expensive calculations"""
    
    def __init__(self, tenant_repository: TenantRepository, cache_ttl: int = 300):
        self._tenant_repository = tenant_repository
        self._cache_ttl = cache_ttl
        self._cache = {}
    
    async def get_average_stay_duration(self, org_id: int) -> float:
        """Cached calculation of average stay duration"""
        cache_key = f"avg_stay_{org_id}"
        
        # Check cache
        if cache_key in self._cache:
            cached_value, timestamp = self._cache[cache_key]
            if datetime.utcnow().timestamp() - timestamp < self._cache_ttl:
                return cached_value
        
        # Calculate and cache
        value = await self._calculate_average_stay_duration(org_id)
        self._cache[cache_key] = (value, datetime.utcnow().timestamp())
        
        return value
    
    async def _calculate_average_stay_duration(self, org_id: int) -> float:
        """Actual calculation logic"""
        # Implementation here
        pass
```

### Batch Processing Pattern

```python
class BatchTenantService:
    """Service for batch tenant operations"""
    
    def __init__(self, tenant_repository: TenantRepository):
        self._tenant_repository = tenant_repository
    
    async def bulk_admit_tenants(self, tenant_ids: List[int], admission_date: datetime):
        """Admit multiple tenants efficiently"""
        # Fetch all tenants in one query
        tenants = []
        for tenant_id in tenant_ids:
            tenant = await self._tenant_repository.get_by_id(tenant_id)
            if tenant and tenant.can_be_admitted():
                tenants.append(tenant)
        
        # Validate all can be admitted
        for tenant in tenants:
            if not tenant.can_be_admitted():
                raise TenantAdmissionError(f"Tenant {tenant.id} cannot be admitted")
        
        # Admit all tenants
        admitted_tenants = []
        for tenant in tenants:
            tenant.admit(admission_date)
            admitted_tenant = await self._tenant_repository.update(tenant)
            admitted_tenants.append(admitted_tenant)
        
        return admitted_tenants
```

## Best Practices

### 1. **Keep Services Focused**

```python
# ✅ Good: Single responsibility
class TenantAdmissionService:
    """Only handles tenant admission logic"""
    pass

# ❌ Bad: Multiple responsibilities
class TenantManagementService:
    """Handles admission, metrics, reporting, billing..."""
    pass
```

### 2. **Use Dependency Injection**

```python
# ✅ Good: Dependencies injected
class TenantService:
    def __init__(self, tenant_repo: TenantRepository, org_repo: OrganizationRepository):
        self._tenant_repo = tenant_repo
        self._org_repo = org_repo

# ❌ Bad: Dependencies created internally
class TenantService:
    def __init__(self):
        self._tenant_repo = SQLTenantRepository()  # Tightly coupled
```

### 3. **Handle Errors Appropriately**

```python
# ✅ Good: Specific, meaningful exceptions
async def admit_tenant(self, tenant_id: int):
    tenant = await self._tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise TenantNotFoundError(f"Tenant {tenant_id} not found")
    
    if not tenant.can_be_admitted():
        raise TenantAdmissionError("Tenant not eligible")

# ❌ Bad: Generic exceptions
async def admit_tenant(self, tenant_id: int):
    try:
        # Logic here
        pass
    except Exception as e:
        raise Exception("Admission failed")  # Not helpful
```

### 4. **Document Business Rules**

```python
async def validate_admission_requirements(self, tenant_id: int) -> bool:
    """
    Business Rules for Tenant Admission:
    1. Tenant must exist
    2. Tenant must be on waitlist
    3. Tenant must not already be admitted
    4. Organization must have available capacity
    5. Admission date must be today or in the future
    """
    # Implementation with clear business rule comments
    pass
```

## Common Patterns

### Policy Pattern

```python
class AdmissionPolicy:
    """Business rules for tenant admission"""
    
    @staticmethod
    def can_admit_tenant(tenant: TenantEntity, org_capacity: int) -> bool:
        """Centralized admission policy"""
        return (tenant.is_waitlist and 
                not tenant.is_currently_admitted() and
                org_capacity > 0)

class TenantAdmissionService:
    def __init__(self, tenant_repo: TenantRepository):
        self._tenant_repo = tenant_repo
    
    async def admit_tenant(self, tenant_id: int, admission_date: datetime):
        tenant = await self._tenant_repo.get_by_id(tenant_id)
        org_capacity = await self._get_org_capacity(tenant.organization_id)
        
        if not AdmissionPolicy.can_admit_tenant(tenant, org_capacity):
            raise TenantAdmissionError("Admission policy violation")
        
        # Proceed with admission
        tenant.admit(admission_date)
        return await self._tenant_repo.update(tenant)
```

### Saga Pattern for Complex Workflows

```python
class TenantAdmissionSaga:
    """Saga pattern for complex admission workflows"""
    
    def __init__(self, 
                 tenant_service: TenantService,
                 org_service: OrganizationService,
                 notification_service):
        self._tenant_service = tenant_service
        self._org_service = org_service
        self._notification_service = notification_service
    
    async def execute_admission_saga(self, tenant_id: int):
        """Execute admission with compensation logic"""
        tenant = None
        try:
            # Step 1: Get tenant
            tenant = await self._tenant_service.get_tenant(tenant_id)
            
            # Step 2: Admit tenant
            admitted_tenant = await self._tenant_service.admit_tenant(
                tenant_id, datetime.utcnow()
            )
            
            # Step 3: Update organization
            await self._org_service.decrement_capacity(admitted_tenant.organization_id)
            
            # Step 4: Send notifications
            await self._notification_service.notify_admission(admitted_tenant)
            
            return admitted_tenant
            
        except Exception as e:
            # Compensation actions
            if tenant and tenant.is_currently_admitted():
                await self._tenant_service.discharge_tenant(tenant_id, datetime.utcnow())
            
            raise SagaExecutionError(f"Admission saga failed: {str(e)}")
```

This pattern ensures domain services contain the core business logic while maintaining clean separation of concerns and testability.
