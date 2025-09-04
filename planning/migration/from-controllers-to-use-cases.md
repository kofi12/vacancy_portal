# 🔄 Migrating from Controllers to Use Cases

## Overview

This guide shows how to extract business logic from FastAPI controllers and move it into Clean Architecture use cases.

## Before vs After Comparison

### ❌ Current Controller (Mixed Concerns)

```python
# controller/tenant_controller.py
@tenant_router.post('/create-tenant')
def create_tenant(
    request: dict, 
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # ❌ HTTP concerns mixed with business logic
    if not request.get('name'):
        raise HTTPException(400, "Name is required")
    
    # ❌ Database concerns in controller
    existing = db.query(Tenant).filter(
        Tenant.name == request['name'],
        Tenant.organization_id == request['organization_id']
    ).first()
    
    if existing:
        raise HTTPException(409, "Tenant already exists")
    
    # ❌ Business logic in controller
    tenant = Tenant(
        name=request['name'],
        organization_id=request['organization_id'],
        waitlist=True
    )
    
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    return {"tenant": tenant, "created": True}
```

### ✅ Clean Architecture Controller

```python
# presentation/controllers/tenant_controller.py
@tenant_router.post('/create-tenant')
@handle_domain_exceptions
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
) -> TenantResponse:
    # ✅ Only HTTP concerns
    return await use_case.execute(request)

# application/use_cases/create_tenant_use_case.py
class CreateTenantUseCase:
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self, request: CreateTenantRequest) -> TenantResponse:
        # ✅ Pure business logic
        tenant = TenantEntity.create_tenant(
            request.name, request.organization_id
        )
        created_tenant = await self._tenant_service.create_tenant(tenant)
        return TenantResponse.from_entity(created_tenant)
```

## Step-by-Step Migration

### Step 1: Extract Request DTO

**Create file:** `application/dto/tenant_dto.py`

```python
class CreateTenantRequest(BaseDTO):
    """Request DTO for creating a tenant"""
    name: str
    organization_id: int
    is_waitlist: bool = False
```

**Update controller:**

```python
@tenant_router.post('/create-tenant')
def create_tenant(request: CreateTenantRequest, ...):  # Use Pydantic model
    # Now we have type safety and validation
    pass
```

### Step 2: Extract Response DTO

**Add to tenant_dto.py:**

```python
class TenantResponse(BaseDTO):
    """Response DTO for tenant data"""
    id: int
    name: str
    admission_date: Optional[datetime] = None
    is_waitlist: bool = False
    organization_id: int
    created_at: datetime
    
    @classmethod
    def from_entity(cls, tenant) -> 'TenantResponse':
        return cls(
            id=tenant.id,
            name=tenant.name,
            admission_date=tenant.admission_date,
            is_waitlist=tenant.is_waitlist,
            organization_id=tenant.organization_id,
            created_at=tenant.created_at
        )
```

### Step 3: Create Use Case

**Create file:** `application/use_cases/create_tenant_use_case.py`

```python
class CreateTenantUseCase:
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self, request: CreateTenantRequest) -> TenantResponse:
        tenant = TenantEntity.create_tenant(
            name=request.name,
            organization_id=request.organization_id,
            is_waitlist=request.is_waitlist
        )
        
        created_tenant = await self._tenant_service.create_tenant(tenant)
        return TenantResponse.from_entity(created_tenant)
```

### Step 4: Update Controller to Use Use Case

**Update controller:**

```python
@tenant_router.post('/create-tenant')
@handle_domain_exceptions
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
) -> TenantResponse:
    return await use_case.execute(request)
```

## Advanced Migration Patterns

### Complex Controller with Multiple Responsibilities

**Before:**

```python
@tenant_router.post('/admit-tenant')
def admit_tenant(
    tenant_id: int, 
    admission_data: dict,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Validation
    if not admission_data.get('admission_date'):
        raise HTTPException(400, "Admission date required")
    
    # Fetch tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(404, "Tenant not found")
    
    # Business logic
    if tenant.admission_date:
        raise HTTPException(400, "Tenant already admitted")
    
    # Authorization
    if current_user.organization_id != tenant.organization_id:
        raise HTTPException(403, "Not authorized")
    
    # Update
    tenant.admission_date = admission_data['admission_date']
    tenant.waitlist = False
    
    db.commit()
    db.refresh(tenant)
    
    return {"tenant": tenant, "admitted": True}
```

**After:**

```python
# DTOs
class AdmitTenantRequest(BaseDTO):
    tenant_id: int
    admission_date: datetime

# Use Case
class AdmitTenantUseCase:
    def __init__(self, tenant_service: TenantService, auth_service):
        self._tenant_service = tenant_service
        self._auth_service = auth_service
    
    async def execute(self, request: AdmitTenantRequest, user_id: int) -> TenantResponse:
        # Authorization
        await self._auth_service.check_tenant_access(user_id, request.tenant_id)
        
        # Business logic
        admitted_tenant = await self._tenant_service.admit_tenant(
            request.tenant_id, request.admission_date
        )
        
        return TenantResponse.from_entity(admitted_tenant)

# Controller
@tenant_router.post('/admit-tenant')
@handle_domain_exceptions
async def admit_tenant(
    request: AdmitTenantRequest,
    current_user: User = Depends(get_current_user),
    use_case: AdmitTenantUseCase = Depends(get_admit_tenant_use_case)
) -> TenantResponse:
    return await use_case.execute(request, current_user.id)
```

## Error Handling Migration

### Before: HTTP Exceptions in Controller

```python
# ❌ Mixed error handling
if not tenant:
    raise HTTPException(404, "Tenant not found")
if tenant.admission_date:
    raise HTTPException(400, "Already admitted")
```

### After: Domain Exceptions with Handler

```python
# ✅ Domain exceptions
class TenantNotFoundError(DomainException):
    pass

class TenantAlreadyAdmittedError(DomainException):
    pass

# ✅ Exception handler decorator
def handle_domain_exceptions(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TenantNotFoundError:
            raise HTTPException(404, "Tenant not found")
        except TenantAlreadyAdmittedError:
            raise HTTPException(400, "Tenant already admitted")
        # ... other exceptions
    return wrapper
```

## Testing Migration

### Before: Hard to Test Controllers

```python
def test_create_tenant():
    # Hard to test - requires database, HTTP setup
    response = client.post("/tenants", json={"name": "Test"})
    assert response.status_code == 200
```

### After: Easy to Test Each Layer

```python
def test_create_tenant_use_case():
    # Easy to test - just business logic
    mock_repo = MagicMock()
    mock_service = TenantService(mock_repo)
    use_case = CreateTenantUseCase(mock_service)
    
    request = CreateTenantRequest(name="Test", organization_id=1)
    result = await use_case.execute(request)
    
    assert result.name == "Test"
    mock_repo.create.assert_called_once()

def test_create_tenant_controller():
    # Test just HTTP concerns
    response = client.post("/v2/tenants", json={"name": "Test", "organization_id": 1})
    assert response.status_code == 200
```

## Authorization Migration

### Before: Authorization in Controller

```python
# ❌ Authorization mixed with business logic
if current_user.organization_id != tenant.organization_id:
    raise HTTPException(403, "Not authorized")
```

### After: Authorization in Use Case or Service

```python
# ✅ Authorization in domain service
class TenantService:
    def __init__(self, tenant_repo: TenantRepository, auth_service):
        self._tenant_repo = tenant_repo
        self._auth_service = auth_service
    
    async def admit_tenant(self, tenant_id: int, user_id: int, admission_date: datetime):
        # Authorization
        await self._auth_service.check_tenant_access(user_id, tenant_id)
        
        # Business logic
        tenant = await self._tenant_repo.get_by_id(tenant_id)
        tenant.admit(admission_date)
        
        return await self._tenant_repo.update(tenant)
```

## Performance Considerations

### Before: N+1 Queries in Controller

```python
# ❌ Inefficient queries
tenants = db.query(Tenant).filter(Tenant.organization_id == org_id).all()
for tenant in tenants:
    org = db.query(Organization).filter(Organization.id == tenant.organization_id).first()
    # N+1 query problem
```

### After: Optimized in Repository

```python
# ✅ Efficient queries in repository
async def get_tenants_with_organizations(self, org_id: int):
    stmt = select(TenantModel, OrganizationModel).join(
        OrganizationModel,
        TenantModel.organization_id == OrganizationModel.id
    ).where(TenantModel.organization_id == org_id)
    
    result = await self._session.execute(stmt)
    return result.all()
```

## Common Migration Challenges

### 1. **Large Controllers**

**Problem:** Controllers with 100+ lines of mixed concerns
**Solution:** Break into multiple use cases, one per business operation

### 2. **Complex Authorization**

**Problem:** Authorization logic scattered across controllers
**Solution:** Create dedicated authorization services

### 3. **Database Transaction Management**

**Problem:** Transaction logic mixed with business logic
**Solution:** Move to repository layer with proper session management

### 4. **External API Calls**

**Problem:** HTTP calls to external services in controllers
**Solution:** Create infrastructure services for external APIs

## Rollback Strategy

### Quick Rollback

```python
# Feature flag for easy rollback
USE_CLEAN_CONTROLLERS = os.getenv('USE_CLEAN_CONTROLLERS', 'false').lower() == 'true'

if USE_CLEAN_CONTROLLERS:
    app.include_router(clean_tenant_router, prefix="/api/v2")
else:
    app.include_router(legacy_tenant_router, prefix="/api/v1")
```

### Gradual Rollback

1. Disable new controllers with feature flag
2. Revert controller changes
3. Keep domain/use case code (it's still valuable)
4. Rollback infrastructure changes if needed

## Success Metrics

### Code Quality Metrics

- ✅ **Controller size**: Reduce from 100+ lines to < 20 lines
- ✅ **Test coverage**: 80%+ coverage for use cases
- ✅ **Separation of concerns**: No business logic in controllers
- ✅ **Error handling**: Centralized exception handling

### Performance Metrics

- ✅ **Response time**: No degradation
- ✅ **Memory usage**: No increase
- ✅ **Database queries**: Optimized query patterns
- ✅ **Concurrent requests**: Handle same or better load

## Next Steps

After migrating controllers:

1. **Remove legacy controllers** (once new ones are proven)
2. **Update API documentation** to reflect new endpoints
3. **Migrate client applications** to use new endpoints
4. **Optimize database queries** based on new access patterns

This migration pattern ensures controllers become thin HTTP adapters while business logic moves to appropriate layers, following Clean Architecture principles.
