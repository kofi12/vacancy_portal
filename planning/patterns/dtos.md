# 📦 Data Transfer Object (DTO) Pattern

## Overview

DTOs are simple objects that carry data between processes, providing a clean contract between layers.

## Key Characteristics

### ✅ DTO Benefits

- **Type Safety**: Strongly typed data structures
- **Validation**: Automatic input validation
- **Documentation**: Self-documenting API contracts
- **Transformation**: Clean data mapping between layers

### ❌ What DTOs Should NOT Do

- **Business Logic**: Keep DTOs simple data containers
- **Database Operations**: No persistence logic
- **Complex Validation**: Keep validation rules simple
- **Inheritance**: Avoid complex inheritance hierarchies

## Basic DTO Patterns

### Request DTO Pattern

```python
# application/dto/tenant_dto.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CreateTenantRequest(BaseModel):
    """DTO for tenant creation requests"""
    
    name: str = Field(..., min_length=1, max_length=100, description="Tenant full name")
    organization_id: int = Field(..., gt=0, description="Organization ID")
    is_waitlist: bool = Field(default=False, description="Whether tenant is on waitlist")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "organization_id": 1,
                "is_waitlist": True
            }
        }
```

### Response DTO Pattern

```python
class TenantResponse(BaseModel):
    """DTO for tenant response data"""
    
    id: int
    created_at: datetime
    name: str
    admission_date: Optional[datetime] = None
    discharge_date: Optional[datetime] = None
    is_waitlist: bool = False
    organization_id: int
    
    @classmethod
    def from_entity(cls, tenant) -> 'TenantResponse':
        """Convert domain entity to response DTO"""
        return cls(
            id=tenant.id,
            created_at=tenant.created_at,
            name=tenant.name,
            admission_date=tenant.admission_date,
            discharge_date=tenant.discharge_date,
            is_waitlist=tenant.is_waitlist,
            organization_id=tenant.organization_id
        )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "id": 1,
                "created_at": "2023-01-01T12:00:00Z",
                "name": "John Doe",
                "admission_date": "2023-01-02T10:00:00Z",
                "discharge_date": None,
                "is_waitlist": False,
                "organization_id": 1
            }
        }
```

### List Response DTO Pattern

```python
from typing import List

class TenantListResponse(BaseModel):
    """DTO for paginated tenant lists"""
    
    tenants: List[TenantResponse]
    total_count: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    
    @classmethod
    def create_paginated(cls, tenants: List[TenantResponse], total_count: int, 
                        page: int = 1, page_size: int = 20) -> 'TenantListResponse':
        """Create paginated response"""
        total_pages = (total_count + page_size - 1) // page_size
        
        return cls(
            tenants=tenants,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
```

## Advanced DTO Patterns

### Nested DTO Pattern

```python
class OrganizationSummary(BaseModel):
    """Nested DTO for organization summary"""
    id: int
    business_name: str
    max_capacity: int

class TenantWithOrganizationResponse(BaseModel):
    """DTO with nested organization data"""
    
    id: int
    name: str
    admission_date: Optional[datetime] = None
    organization: OrganizationSummary
    
    @classmethod
    def from_entity_with_org(cls, tenant, organization) -> 'TenantWithOrganizationResponse':
        """Convert tenant and organization to nested DTO"""
        return cls(
            id=tenant.id,
            name=tenant.name,
            admission_date=tenant.admission_date,
            organization=OrganizationSummary(
                id=organization.id,
                business_name=organization.business_name,
                max_capacity=organization.max_capacity
            )
        )
```

### Partial Update DTO Pattern

```python
class UpdateTenantRequest(BaseModel):
    """DTO for partial tenant updates"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_waitlist: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Name",
                "is_waitlist": False
            }
        }
    
    def has_updates(self) -> bool:
        """Check if any fields are being updated"""
        return any([
            self.name is not None,
            self.is_waitlist is not None
        ])
    
    def apply_to_entity(self, tenant) -> None:
        """Apply updates to domain entity"""
        if self.name is not None:
            tenant.name = self.name
        if self.is_waitlist is not None:
            tenant.is_waitlist = self.is_waitlist
```

### Search/Filter DTO Pattern

```python
from enum import Enum

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class TenantSortField(str, Enum):
    NAME = "name"
    CREATED_AT = "created_at"
    ADMISSION_DATE = "admission_date"

class TenantSearchRequest(BaseModel):
    """DTO for tenant search/filter requests"""
    
    organization_id: Optional[int] = None
    is_waitlist: Optional[bool] = None
    name_contains: Optional[str] = None
    admitted_after: Optional[datetime] = None
    admitted_before: Optional[datetime] = None
    
    # Pagination
    page: int = Field(default=1, gt=0)
    page_size: int = Field(default=20, gt=0, le=100)
    
    # Sorting
    sort_by: TenantSortField = TenantSortField.CREATED_AT
    sort_order: SortOrder = SortOrder.DESC
    
    def to_query_params(self) -> dict:
        """Convert to query parameters for repository"""
        params = {
            'page': self.page,
            'page_size': self.page_size,
            'sort_by': self.sort_by.value,
            'sort_order': self.sort_order.value
        }
        
        # Add filters if provided
        if self.organization_id:
            params['organization_id'] = self.organization_id
        if self.is_waitlist is not None:
            params['is_waitlist'] = self.is_waitlist
        if self.name_contains:
            params['name_contains'] = self.name_contains
        if self.admitted_after:
            params['admitted_after'] = self.admitted_after
        if self.admitted_before:
            params['admitted_before'] = self.admitted_before
        
        return params
```

## Validation Patterns

### Custom Validator Pattern

```python
from pydantic import validator

class EmailRequest(BaseModel):
    """DTO with custom email validation"""
    
    email: str
    
    @validator('email')
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError('Invalid email format')
        
        # Additional email validation
        local, domain = v.split('@', 1)
        if not local or not domain or '.' not in domain:
            raise ValueError('Invalid email format')
        
        return v.lower().strip()
```

### Cross-Field Validation Pattern

```python
class DateRangeRequest(BaseModel):
    """DTO with cross-field validation"""
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v
```

### Conditional Validation Pattern

```python
class AdmissionRequest(BaseModel):
    """DTO with conditional validation"""
    
    tenant_id: int
    admission_date: datetime
    notes: Optional[str] = None
    
    @validator('notes')
    def validate_notes_required_for_past_admission(cls, v, values):
        """Notes required if admission date is in the past"""
        if (values.get('admission_date') and 
            values['admission_date'] < datetime.utcnow() and 
            not v):
            raise ValueError('Notes required for past admission dates')
        return v
```

## Transformation Patterns

### Entity to DTO Transformation

```python
class DTOMapper:
    """Utility class for entity to DTO transformations"""
    
    @staticmethod
    def tenant_to_response(tenant) -> TenantResponse:
        """Transform tenant entity to response DTO"""
        return TenantResponse(
            id=tenant.id,
            created_at=tenant.created_at,
            name=tenant.name,
            admission_date=tenant.admission_date,
            discharge_date=tenant.discharge_date,
            is_waitlist=tenant.is_waitlist,
            organization_id=tenant.organization_id
        )
    
    @staticmethod
    def tenants_to_list_response(tenants: List, total_count: int, 
                               page: int = 1, page_size: int = 20) -> TenantListResponse:
        """Transform tenant list to paginated response"""
        tenant_dtos = [DTOMapper.tenant_to_response(t) for t in tenants]
        return TenantListResponse.create_paginated(
            tenant_dtos, total_count, page, page_size
        )
```

### DTO to Entity Transformation

```python
class EntityMapper:
    """Utility class for DTO to entity transformations"""
    
    @staticmethod
    def create_tenant_request_to_entity(request: CreateTenantRequest) -> TenantEntity:
        """Transform create request to tenant entity"""
        return TenantEntity.create_tenant(
            name=request.name,
            organization_id=request.organization_id,
            is_waitlist=request.is_waitlist
        )
    
    @staticmethod
    def update_tenant_request_to_entity(request: UpdateTenantRequest, 
                                      existing_tenant: TenantEntity) -> TenantEntity:
        """Apply update request to existing tenant entity"""
        if request.name is not None:
            existing_tenant.name = request.name
        if request.is_waitlist is not None:
            existing_tenant.is_waitlist = request.is_waitlist
        
        return existing_tenant
```

## API Documentation Patterns

### OpenAPI Schema Enhancement

```python
class DetailedTenantResponse(BaseModel):
    """Enhanced response DTO with detailed OpenAPI documentation"""
    
    id: int = Field(..., description="Unique tenant identifier")
    created_at: datetime = Field(..., description="When tenant was created")
    name: str = Field(..., min_length=1, max_length=100, description="Tenant full name")
    admission_date: Optional[datetime] = Field(None, description="When tenant was admitted")
    discharge_date: Optional[datetime] = Field(None, description="When tenant was discharged")
    is_waitlist: bool = Field(False, description="Whether tenant is on waitlist")
    organization_id: int = Field(..., gt=0, description="Organization identifier")
    
    class Config:
        title = "Tenant"
        description = "Complete tenant information"
        json_schema_extra = {
            "example": {
                "id": 1,
                "created_at": "2023-01-01T12:00:00Z",
                "name": "John Doe",
                "admission_date": "2023-01-02T10:00:00Z",
                "discharge_date": None,
                "is_waitlist": False,
                "organization_id": 1
            }
        }
```

## Testing Patterns

### DTO Unit Testing

```python
def test_create_tenant_request_validation():
    """Test DTO validation"""
    # Valid request
    request = CreateTenantRequest(
        name="John Doe",
        organization_id=1,
        is_waitlist=True
    )
    assert request.name == "John Doe"
    
    # Invalid name
    with pytest.raises(ValidationError):
        CreateTenantRequest(name="", organization_id=1)
    
    # Invalid organization ID
    with pytest.raises(ValidationError):
        CreateTenantRequest(name="John Doe", organization_id=0)

def test_tenant_response_from_entity():
    """Test entity to DTO transformation"""
    tenant = TenantEntity(
        id=1,
        created_at=datetime(2023, 1, 1),
        name="Test Tenant",
        organization_id=1
    )
    
    response = TenantResponse.from_entity(tenant)
    
    assert response.id == 1
    assert response.name == "Test Tenant"
    assert response.organization_id == 1
```

### DTO Integration Testing

```python
def test_dto_serialization():
    """Test DTO JSON serialization"""
    response = TenantResponse(
        id=1,
        created_at=datetime(2023, 1, 1),
        name="Test Tenant",
        organization_id=1
    )
    
    json_data = response.model_dump_json()
    parsed = json.loads(json_data)
    
    assert parsed['id'] == 1
    assert parsed['name'] == "Test Tenant"
    assert 'created_at' in parsed  # datetime serialized
```

## Best Practices

### 1. **Keep DTOs Simple**

```python
# ✅ Good: Simple, focused DTO
class CreateTenantRequest(BaseModel):
    name: str
    organization_id: int

# ❌ Bad: Overcomplicated DTO
class CreateTenantRequest(BaseModel):
    name: str
    organization_id: int
    created_by_user_id: int
    ip_address: str
    user_agent: str
    # ... many irrelevant fields
```

### 2. **Use Consistent Naming**

```python
# ✅ Good: Consistent naming pattern
class CreateTenantRequest(BaseModel): pass
class UpdateTenantRequest(BaseModel): pass
class TenantResponse(BaseModel): pass

# ❌ Bad: Inconsistent naming
class TenantCreateRequest(BaseModel): pass
class UpdateTenantDTO(BaseModel): pass
class TenantDataResponse(BaseModel): pass
```

### 3. **Document with Examples**

```python
# ✅ Good: Well-documented with examples
class CreateTenantRequest(BaseModel):
    name: str = Field(..., description="Tenant full name", example="John Doe")
    organization_id: int = Field(..., description="Organization ID", example=1)

# ❌ Bad: Poor documentation
class CreateTenantRequest(BaseModel):
    name: str
    organization_id: int
```

### 4. **Validate at Boundaries**

```python
# ✅ Good: Validation in DTO
class CreateTenantRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    organization_id: int = Field(gt=0)

# ❌ Bad: No validation
class CreateTenantRequest(BaseModel):
    name: str
    organization_id: int
```

### 5. **Avoid Business Logic in DTOs**

```python
# ✅ Good: DTO is just data
class TenantResponse(BaseModel):
    name: str
    is_admitted: bool

# ❌ Bad: Business logic in DTO
class TenantResponse(BaseModel):
    name: str
    
    @property
    def is_admitted(self) -> bool:
        # Business logic doesn't belong here
        return self.admission_date is not None
```

## Common Patterns

### API Versioning with DTOs

```python
# v1 DTO
class TenantResponseV1(BaseModel):
    id: int
    name: str
    organization_id: int

# v2 DTO with additional fields
class TenantResponseV2(BaseModel):
    id: int
    name: str
    organization_id: int
    admission_date: Optional[datetime] = None
    is_waitlist: bool = False

# Controller uses appropriate version
@tenant_router.get("/tenants", response_model=List[TenantResponseV2])
async def get_tenants_v2():
    # Use V2 DTO
    pass

@tenant_router.get("/v1/tenants", response_model=List[TenantResponseV1])
async def get_tenants_v1():
    # Use V1 DTO
    pass
```

### Error Response DTOs

```python
class ErrorResponse(BaseModel):
    """Standard error response DTO"""
    error_code: str
    message: str
    details: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "TENANT_NOT_FOUND",
                "message": "Tenant with ID 123 not found",
                "details": {"tenant_id": 123}
            }
        }

# Usage in exception handlers
def handle_domain_exceptions(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TenantNotFoundError as e:
            return JSONResponse(
                status_code=404,
                content=ErrorResponse(
                    error_code="TENANT_NOT_FOUND",
                    message=str(e),
                    details={"tenant_id": e.tenant_id}
                ).model_dump()
            )
```

This pattern ensures DTOs provide clean, validated data contracts between layers while maintaining separation of concerns.
