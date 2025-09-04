# 🌐 API Design Pattern

## Overview

API design patterns ensure consistent, intuitive, and maintainable REST APIs that align with Clean Architecture principles.

## RESTful Resource Patterns

### Resource Naming Convention

```python
# ✅ Good: Consistent resource naming
GET    /api/v2/tenants           # List tenants
POST   /api/v2/tenants           # Create tenant
GET    /api/v2/tenants/{id}      # Get specific tenant
PUT    /api/v2/tenants/{id}      # Update tenant
DELETE /api/v2/tenants/{id}      # Delete tenant

GET    /api/v2/tenants/{id}/admit # Admit tenant
POST   /api/v2/tenants/search     # Search tenants
GET    /api/v2/organizations/{org_id}/tenants # Get org tenants

# ❌ Bad: Inconsistent naming
GET    /api/v2/getAllTenants
POST   /api/v2/createTenant
GET    /api/v2/tenantDetails/{id}
PUT    /api/v2/modifyTenant/{id}
```

### Nested Resource Pattern

```python
# Organization tenants
GET    /api/v2/organizations/{org_id}/tenants
POST   /api/v2/organizations/{org_id}/tenants
GET    /api/v2/organizations/{org_id}/tenants/{tenant_id}

# Tenant admissions
POST   /api/v2/tenants/{tenant_id}/admissions
GET    /api/v2/tenants/{tenant_id}/admissions
DELETE /api/v2/tenants/{tenant_id}/admissions/{admission_id}
```

## HTTP Status Code Patterns

### Success Responses

```python
# 200 OK - Successful GET/PUT/PATCH
@app.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: int):
    tenant = await get_tenant_use_case.execute(tenant_id)
    return TenantResponse.from_entity(tenant)

# 201 Created - Successful POST
@app.post("/tenants", status_code=201)
async def create_tenant(request: CreateTenantRequest):
    tenant = await create_tenant_use_case.execute(request)
    return TenantResponse.from_entity(tenant)

# 204 No Content - Successful DELETE
@app.delete("/tenants/{tenant_id}", status_code=204)
async def delete_tenant(tenant_id: int):
    await delete_tenant_use_case.execute(tenant_id)
    return Response(status_code=204)
```

### Error Response Pattern

```python
# Standard error response structure
class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "TENANT_NOT_FOUND",
                "message": "Tenant with ID 123 not found",
                "details": {"tenant_id": 123},
                "timestamp": "2023-01-01T12:00:00Z"
            }
        }

# Error handling decorator
def handle_domain_exceptions(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TenantNotFoundError as e:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error_code="TENANT_NOT_FOUND",
                    message=str(e),
                    details={"tenant_id": e.tenant_id}
                ).model_dump()
            )
        except TenantAlreadyExistsError as e:
            raise HTTPException(
                status_code=409,
                detail=ErrorResponse(
                    error_code="TENANT_ALREADY_EXISTS",
                    message=str(e),
                    details={"tenant_name": e.tenant_name}
                ).model_dump()
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail=ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message="Request validation failed",
                    details=e.errors()
                ).model_dump()
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=ErrorResponse(
                    error_code="INTERNAL_SERVER_ERROR",
                    message="An unexpected error occurred"
                ).model_dump()
            )
    
    return wrapper
```

## Request/Response Patterns

### Pagination Pattern

```python
class PaginationRequest(BaseModel):
    page: int = Field(1, gt=0, description="Page number")
    page_size: int = Field(20, gt=0, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: str = Field("asc", regex="^(asc|desc)$", description="Sort order")

class PaginatedResponse(BaseModel):
    items: List[Any]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def create(cls, items: List[Any], total_count: int, 
               page: int, page_size: int) -> 'PaginatedResponse':
        total_pages = (total_count + page_size - 1) // page_size
        return cls(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )

# Controller implementation
@app.get("/tenants", response_model=PaginatedResponse)
async def get_tenants(pagination: PaginationRequest = Depends()):
    tenants, total_count = await get_tenants_use_case.execute(
        page=pagination.page,
        page_size=pagination.page_size,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order
    )
    
    return PaginatedResponse.create(
        items=[TenantResponse.from_entity(t) for t in tenants],
        total_count=total_count,
        page=pagination.page,
        page_size=pagination.page_size
    )
```

### Filtering and Search Pattern

```python
class TenantFilterRequest(BaseModel):
    organization_id: Optional[int] = None
    is_waitlist: Optional[bool] = None
    admitted_after: Optional[datetime] = None
    admitted_before: Optional[datetime] = None
    name_contains: Optional[str] = None

# Combined request
class GetTenantsRequest(PaginationRequest, TenantFilterRequest):
    pass

# Usage
@app.get("/tenants")
async def get_tenants(request: GetTenantsRequest = Depends()):
    # Convert to domain filters
    filters = {
        k: v for k, v in request.dict().items() 
        if v is not None and k not in ['page', 'page_size', 'sort_by', 'sort_order']
    }
    
    # Execute use case
    result = await get_tenants_use_case.execute(
        page=request.page,
        page_size=request.page_size,
        filters=filters,
        sort_by=request.sort_by,
        sort_order=request.sort_order
    )
    
    return result
```

## API Versioning Patterns

### URL Path Versioning

```python
# Version in URL path
@app.get("/api/v1/tenants")
async def get_tenants_v1():
    # V1 implementation
    pass

@app.get("/api/v2/tenants") 
async def get_tenants_v2():
    # V2 implementation with new features
    pass

# Accept header versioning
@app.get("/tenants")
async def get_tenants(accept: str = Header("application/vnd.api.v1+json")):
    if "v2" in accept:
        # V2 implementation
        pass
    else:
        # V1 implementation
        pass
```

### Semantic Versioning Strategy

```python
# PATCH versions (1.0.0 -> 1.0.1): Bug fixes, no API changes
# MINOR versions (1.0.0 -> 1.1.0): New features, backward compatible
# MAJOR versions (1.0.0 -> 2.0.0): Breaking changes

# Version headers
@app.get("/tenants")
async def get_tenants(
    x_api_version: str = Header("1.0", description="API version")
):
    version = tuple(map(int, x_api_version.split(".")))
    major, minor, patch = version + (0,) * (3 - len(version))
    
    if major >= 2:
        # V2 features
        pass
    elif minor >= 1:
        # V1.1 features
        pass
    else:
        # V1.0 features
        pass
```

## Content Negotiation Patterns

### Accept Header Pattern

```python
from fastapi.responses import JSONResponse, XMLResponse

@app.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: int,
    accept: str = Header("application/json")
):
    tenant = await get_tenant_use_case.execute(tenant_id)
    
    if "application/xml" in accept:
        # Return XML response
        xml_content = f"<tenant><id>{tenant.id}</id><name>{tenant.name}</name></tenant>"
        return XMLResponse(content=xml_content)
    else:
        # Return JSON response (default)
        return TenantResponse.from_entity(tenant)
```

### Response Format Parameter

```python
@app.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: int,
    format: str = Query("json", regex="^(json|xml|csv)$")
):
    tenant = await get_tenant_use_case.execute(tenant_id)
    
    if format == "xml":
        xml_content = f"<tenant><id>{tenant.id}</id><name>{tenant.name}</name></tenant>"
        return XMLResponse(content=xml_content)
    elif format == "csv":
        csv_content = f"id,name\n{tenant.id},{tenant.name}"
        return Response(content=csv_content, media_type="text/csv")
    else:
        return TenantResponse.from_entity(tenant)
```

## Authentication and Authorization Patterns

### JWT Token Pattern

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/tenants")
async def create_tenant(
    request: CreateTenantRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Validate token
    token_data = await validate_token_use_case.execute(credentials.credentials)
    
    # Check permissions
    await check_permissions_use_case.execute(
        token_data.user_id, 
        "create_tenant",
        request.organization_id
    )
    
    # Execute business logic
    tenant = await create_tenant_use_case.execute(request)
    return TenantResponse.from_entity(tenant)
```

### API Key Pattern

```python
@app.post("/tenants")
async def create_tenant(
    request: CreateTenantRequest,
    api_key: str = Header(..., alias="X-API-Key")
):
    # Validate API key
    await validate_api_key_use_case.execute(api_key)
    
    # Execute business logic
    tenant = await create_tenant_use_case.execute(request)
    return TenantResponse.from_entity(tenant)
```

## Rate Limiting Patterns

### Token Bucket Pattern

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/tenants")
@limiter.limit("10/minute")
async def create_tenant(request: CreateTenantRequest):
    # Rate limited to 10 requests per minute per IP
    tenant = await create_tenant_use_case.execute(request)
    return TenantResponse.from_entity(tenant)
```

### User-Based Rate Limiting

```python
@app.post("/tenants")
async def create_tenant(
    request: CreateTenantRequest,
    current_user: User = Depends(get_current_user)
):
    # Check user-specific rate limits
    await check_rate_limit_use_case.execute(
        current_user.id, 
        "create_tenant", 
        max_requests=50, 
        window_minutes=60
    )
    
    tenant = await create_tenant_use_case.execute(request)
    return TenantResponse.from_entity(tenant)
```

## Caching Patterns

### Response Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="api-cache")

@app.get("/tenants/{tenant_id}")
@FastAPICache.get(expire=300)  # Cache for 5 minutes
async def get_tenant(tenant_id: int):
    return await get_tenant_use_case.execute(tenant_id)
```

### Conditional Caching

```python
@app.get("/tenants")
async def get_tenants(
    request: GetTenantsRequest = Depends(),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match")
):
    # Generate ETag based on data
    etag = await generate_etag_use_case.execute(request)
    
    if if_none_match == etag:
        return Response(status_code=304)  # Not Modified
    
    tenants = await get_tenants_use_case.execute(request)
    
    return JSONResponse(
        content=tenants.model_dump(),
        headers={"ETag": etag}
    )
```

## Documentation Patterns

### OpenAPI Enhancement

```python
from fastapi import FastAPI

app = FastAPI(
    title="Vacancy Portal API",
    description="""
    Clean Architecture implementation of Vacancy Portal API.
    
    ## Features
    
    * **Tenant Management**: Complete CRUD operations for tenants
    * **Organization Support**: Multi-tenant architecture
    * **Waitlist Management**: Automated admission workflows
    * **Authentication**: JWT-based authentication
    * **Authorization**: Role-based access control
    
    ## Getting Started
    
    1. Obtain an API key from `/auth/login`
    2. Include the token in `Authorization: Bearer {token}` header
    3. Start making requests to the API endpoints
    """,
    version="2.0.0",
    contact={
        "name": "API Support",
        "email": "support@vacancyportal.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Enhanced endpoint documentation
@app.post(
    "/tenants",
    response_model=TenantResponse,
    summary="Create a new tenant",
    description="""
    Creates a new tenant in the system.
    
    **Business Rules:**
    - Tenant name must be unique within the organization
    - Organization must exist and be active
    - User must have permission to create tenants in the organization
    
    **Side Effects:**
    - Sends notification to organization administrators
    - Updates organization's tenant count
    """,
    responses={
        201: {"description": "Tenant created successfully"},
        409: {"description": "Tenant already exists"},
        403: {"description": "Insufficient permissions"}
    }
)
async def create_tenant(request: CreateTenantRequest):
    pass
```

## Testing Patterns

### API Integration Testing

```python
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_create_tenant_success(client):
    """Test successful tenant creation"""
    response = client.post(
        "/api/v2/tenants",
        json={
            "name": "John Doe",
            "organization_id": 1,
            "is_waitlist": True
        },
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["is_waitlist"] == True
    assert "id" in data

def test_create_tenant_validation_error(client):
    """Test tenant creation with validation error"""
    response = client.post(
        "/api/v2/tenants",
        json={
            "name": "",  # Invalid: empty name
            "organization_id": 1
        }
    )
    
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"] == ["body", "name"] for error in errors)

def test_get_tenant_not_found(client):
    """Test getting non-existent tenant"""
    response = client.get("/api/v2/tenants/999")
    
    assert response.status_code == 404
    error = response.json()
    assert error["error_code"] == "TENANT_NOT_FOUND"
```

### Contract Testing

```python
def test_api_contract_compliance(client):
    """Test that API responses match expected schema"""
    response = client.get("/api/v2/tenants/1")
    
    # Validate response structure
    schema = TenantResponse.model_json_schema()
    validate(instance=response.json(), schema=schema)
    
    # Validate required fields
    data = response.json()
    required_fields = ["id", "name", "organization_id", "is_waitlist"]
    for field in required_fields:
        assert field in data
```

This pattern ensures APIs are consistent, well-documented, and follow RESTful conventions while maintaining Clean Architecture principles.
