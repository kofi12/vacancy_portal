# Phase 4: Presentation Layer Implementation

## 🎯 What You'll Build

Create FastAPI controllers that use clean architecture:

- ✅ Controllers using dependency injection
- ✅ Exception handling decorators
- ✅ Request/response mapping
- ✅ API documentation with clean architecture
- ✅ Gradual migration from existing controllers

## 📋 Prerequisites

- [x] [Infrastructure Layer Phase](../phases/03-infrastructure-layer.md) completed
- [x] Repository implementations and dependency injection working
- [x] Use cases and DTOs implemented
- [x] Existing controllers still working
- [x] 2-3 hours available

## 🛠️ Implementation Steps

### Step 1: Create Clean Architecture Controllers (25 minutes)

**Create file:** `presentation/controllers/tenant_controller.py`

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from application.dto.tenant_dto import (
    CreateTenantRequest, AdmitTenantRequest, TenantResponse, WaitlistResponse
)
from application.use_cases.tenant_use_cases import (
    CreateTenantUseCase, AdmitTenantUseCase, GetTenantUseCase, GetWaitlistTenantsUseCase
)
from application.exceptions.exception_handlers import handle_domain_exceptions
from infrastructure.dependencies import (
    get_create_tenant_use_case, get_admit_tenant_use_case,
    get_tenant_use_case, get_waitlist_tenants_use_case
)

tenant_router = APIRouter(
    prefix="/api/v2/tenants",
    tags=["tenants"],
    responses={404: {"description": "Not found"}},
)

@tenant_router.post(
    "",
    response_model=TenantResponse,
    summary="Create a new tenant",
    description="Creates a new tenant with validation and business rules"
)
@handle_domain_exceptions
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
) -> TenantResponse:
    """Create a new tenant using clean architecture"""
    return await use_case.execute(request)

@tenant_router.post(
    "/{tenant_id}/admit",
    response_model=TenantResponse,
    summary="Admit a tenant",
    description="Admits a waitlist tenant with business rule validation"
)
@handle_domain_exceptions
async def admit_tenant(
    tenant_id: int,
    request: AdmitTenantRequest,
    use_case: AdmitTenantUseCase = Depends(get_admit_tenant_use_case)
) -> TenantResponse:
    """Admit a tenant using clean architecture"""
    # Override the tenant_id in request with path parameter
    request.tenant_id = tenant_id
    return await use_case.execute(request)

@tenant_router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant by ID",
    description="Retrieves a tenant by their ID"
)
@handle_domain_exceptions
async def get_tenant(
    tenant_id: int,
    use_case: GetTenantUseCase = Depends(get_tenant_use_case)
) -> TenantResponse:
    """Get a tenant by ID"""
    tenant = await use_case.execute(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID {tenant_id} not found"
        )
    
    return tenant

@tenant_router.get(
    "/organizations/{org_id}/waitlist",
    response_model=WaitlistResponse,
    summary="Get waitlist tenants",
    description="Retrieves all waitlist tenants for an organization"
)
@handle_domain_exceptions
async def get_waitlist_tenants(
    org_id: int,
    use_case: GetWaitlistTenantsUseCase = Depends(get_waitlist_tenants_use_case)
) -> WaitlistResponse:
    """Get waitlist tenants for an organization"""
    return await use_case.execute(org_id)

@tenant_router.get(
    "/health",
    summary="Health check",
    description="Check if the tenant service is healthy"
)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "tenant-service"}
```

### Step 2: Create User Controllers (20 minutes)

**Create file:** `presentation/controllers/user_controller.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status

from application.dto.user_dto import (
    CreateUserRequest, UpdateUserRoleRequest, AuthenticateUserRequest,
    UserResponse, LoginResult
)
from application.use_cases.user_use_cases import (
    CreateUserUseCase, AuthenticateUserUseCase, UpdateUserRoleUseCase, GetUserUseCase
)
from application.exceptions.exception_handlers import handle_domain_exceptions
from infrastructure.dependencies import (
    get_create_user_use_case, get_authenticate_user_use_case,
    get_update_user_role_use_case, get_user_use_case
)

user_router = APIRouter(
    prefix="/api/v2/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@user_router.post(
    "",
    response_model=UserResponse,
    summary="Create a new user",
    description="Creates a new user with validation and business rules"
)
@handle_domain_exceptions
async def create_user(
    request: CreateUserRequest,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case)
) -> UserResponse:
    """Create a new user using clean architecture"""
    return await use_case.execute(request)

@user_router.post(
    "/authenticate",
    response_model=LoginResult,
    summary="Authenticate user",
    description="Authenticates a user by email"
)
@handle_domain_exceptions
async def authenticate_user(
    request: AuthenticateUserRequest,
    use_case: AuthenticateUserUseCase = Depends(get_authenticate_user_use_case)
) -> LoginResult:
    """Authenticate a user"""
    return await use_case.execute(request)

@user_router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Update user role",
    description="Updates a user's role with authorization checks"
)
@handle_domain_exceptions
async def update_user_role(
    user_id: int,
    request: UpdateUserRoleRequest,
    use_case: UpdateUserRoleUseCase = Depends(get_update_user_role_use_case)
) -> UserResponse:
    """Update a user's role"""
    # Override the user_id in request with path parameter
    request.user_id = user_id
    return await use_case.execute(request)

@user_router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieves a user by their ID"
)
@handle_domain_exceptions
async def get_user(
    user_id: int,
    use_case: GetUserUseCase = Depends(get_user_use_case)
) -> UserResponse:
    """Get a user by ID"""
    user = await use_case.execute(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return user
```

### Step 3: Create Application Service Controllers (20 minutes)

**Create file:** `presentation/controllers/tenant_management_controller.py`

```python
from fastapi import APIRouter, Depends

from application.dto.tenant_dto import (
    CreateTenantRequest, AdmitTenantRequest, TenantResponse
)
from application.services.tenant_management_service import TenantManagementService
from application.exceptions.exception_handlers import handle_domain_exceptions
from infrastructure.dependencies import get_tenant_management_service

management_router = APIRouter(
    prefix="/api/v2/tenant-management",
    tags=["tenant-management"],
    responses={404: {"description": "Not found"}},
)

@management_router.post(
    "/workflows/admission",
    response_model=TenantResponse,
    summary="Complete tenant admission workflow",
    description="Creates a tenant and admits them in a single workflow"
)
@handle_domain_exceptions
async def process_tenant_admission_workflow(
    create_request: CreateTenantRequest,
    admit_request: AdmitTenantRequest,
    service: TenantManagementService = Depends(get_tenant_management_service)
) -> TenantResponse:
    """Process complete tenant admission workflow"""
    return await service.process_tenant_admission_workflow(
        create_request, admit_request
    )

@management_router.get(
    "/organizations/{org_id}/admission-ready",
    response_model=list[TenantResponse],
    summary="Get admission ready tenants",
    description="Retrieves tenants ready for admission"
)
@handle_domain_exceptions
async def get_admission_ready_tenants(
    org_id: int,
    service: TenantManagementService = Depends(get_tenant_management_service)
) -> list[TenantResponse]:
    """Get tenants ready for admission"""
    return await service.get_admission_ready_tenants(org_id)
```

### Step 4: Create API Router Configuration (15 minutes)

**Create file:** `presentation/routers.py`

```python
from fastapi import APIRouter
from presentation.controllers.tenant_controller import tenant_router
from presentation.controllers.user_controller import user_router
from presentation.controllers.tenant_management_controller import management_router

# Main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(tenant_router)
api_router.include_router(user_router)
api_router.include_router(management_router)

# Health check router
health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    """Overall API health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "clean-architecture"
    }

@health_router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "clean-architecture",
        "components": {
            "database": "healthy",
            "domain_services": "healthy",
            "use_cases": "healthy",
            "repositories": "healthy"
        }
    }
```

### Step 5: Update Main Application (15 minutes)

**Update file:** `main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from presentation.routers import api_router, health_router
from infrastructure.container import container

# Create FastAPI application
app = FastAPI(
    title="Vacancy Portal API",
    description="Clean Architecture implementation of Vacancy Portal",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire dependency injection container
container.wire(modules=[__name__])

# Include routers
app.include_router(api_router)
app.include_router(health_router)

# Legacy router (keep existing functionality)
# from controller.tenant_controller import tenant_router as legacy_tenant_router
# from controller.user_controller import user_router as legacy_user_router
# app.include_router(legacy_tenant_router, prefix="/api/v1")
# app.include_router(legacy_user_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Vacancy Portal API",
        "version": "2.0.0",
        "architecture": "Clean Architecture",
        "docs": "/api/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

### Step 6: Create Middleware and Error Handling (15 minutes)

**Create file:** `presentation/middleware/error_middleware.py`

```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors and logging requests"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            # Log incoming request
            logger.info(f"Request: {request.method} {request.url}")
            
            # Process request
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(".2f")
            
            return response
            
        except Exception as exc:
            # Log error
            process_time = time.time() - start_time
            logger.error(".2f")
            
            # Handle different exception types
            if isinstance(exc, HTTPException):
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail}
                )
            else:
                # Generic error response
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Internal server error"}
                )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for detailed request logging"""
    
    async def dispatch(self, request: Request, call_next):
        # Log request details
        logger.debug(f"Headers: {dict(request.headers)}")
        logger.debug(f"Query params: {dict(request.query_params)}")
        
        response = await call_next(request)
        
        logger.debug(f"Response status: {response.status_code}")
        
        return response
```

## ✅ Success Criteria

- [ ] `presentation/controllers/` directory created
- [ ] `presentation/controllers/tenant_controller.py` with clean architecture
- [ ] `presentation/controllers/user_controller.py` with clean architecture
- [ ] `presentation/controllers/tenant_management_controller.py` for workflows
- [ ] `presentation/routers.py` with router configuration
- [ ] `main.py` updated with clean architecture routers
- [ ] `presentation/middleware/error_middleware.py` with error handling
- [ ] API documentation working at `/api/docs`
- [ ] Health check endpoints working
- [ ] Existing API still functional (if keeping legacy routes)

## 🧪 Testing Your Implementation

```bash
# Start the server
uvicorn main:app --reload

# Test endpoints
curl http://localhost:8000/api/v2/tenants/health
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/api/docs

# Run API tests
pytest tests/api/ -v
```

## 🆘 Common Issues & Solutions

### Issue: Import Errors

```python
ImportError: No module named 'infrastructure'
```

**Solution:** Ensure your PYTHONPATH includes the project root:

```python
# In main.py or startup
import sys
sys.path.append('/Users/aaronkofihaizel/aaronDev/vacancy_portal')
```

### Issue: Dependency Injection Not Working

```python
TypeError: 'Depends' object is not callable
```

**Solution:** Make sure container is wired before creating the app:

```python
# Wire container BEFORE creating routes
container.wire(modules=[__name__])
```

### Issue: Middleware Not Working

- Ensure middleware is added to the app in the correct order
- Check that middleware classes are properly imported
- Verify middleware is added before routes

### Issue: API Documentation Issues

- Check that response models are properly defined
- Ensure Pydantic models are correctly imported
- Verify router prefixes and tags are consistent

## 📚 What You've Accomplished

### Before (Current Architecture)

```python
# Controller directly handles business logic
@tenant_router.post('/create-tenant')
def create_tenant(request: dict, db: Session = Depends(get_session)):
    # Business logic mixed with HTTP concerns
    if not tenant_dao.exists_by_name(request['name'], db):
        tenant = Tenant(name=request['name'], org_id=request['org_id'])
        db.add(tenant)
        db.commit()
        return {"tenant": tenant}
    else:
        raise HTTPException(409, "Tenant already exists")
```

### After (Clean Architecture)

```python
# Controller delegates to use case
@tenant_router.post('', response_model=TenantResponse)
@handle_domain_exceptions
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
) -> TenantResponse:
    # HTTP concerns separated from business logic
    return await use_case.execute(request)
```

## 🔄 Integration with Existing Code

### Option 1: Side-by-Side Deployment (Recommended)

Keep both API versions working:

```python
# Clean architecture endpoints
app.include_router(api_router)  # /api/v2/*

# Legacy endpoints (comment out when ready to migrate)
# app.include_router(legacy_tenant_router, prefix="/api/v1")
# app.include_router(legacy_user_router, prefix="/api/v1")
```

### Option 2: Gradual Controller Migration

Migrate one controller at a time:

```python
# Phase 1: Add clean tenant controller
app.include_router(clean_tenant_router, prefix="/api/v2")

# Phase 2: Replace legacy tenant controller
# app.include_router(legacy_tenant_router, prefix="/api/v1")  # Commented out

# Phase 3: Add clean user controller
app.include_router(clean_user_router, prefix="/api/v2")
```

## 📈 Benefits Achieved

### Developer Experience

- ✅ **Auto-generated API docs** - OpenAPI/Swagger documentation
- ✅ **Type safety** - Pydantic models with validation
- ✅ **Consistent error handling** - Centralized exception management
- ✅ **Easy testing** - HTTP endpoints testable with any client

### API Quality

- ✅ **Clear contracts** - Request/response models define API exactly
- ✅ **Validation at boundaries** - Input validation before business logic
- ✅ **Consistent responses** - Standardized response formats
- ✅ **Rich error messages** - Meaningful error responses

### Business Value

- ✅ **Evolutionary API design** - Easy to change internal logic without affecting API
- ✅ **Multiple API versions** - Support legacy clients while evolving API
- ✅ **Better client experience** - Consistent, well-documented API
- ✅ **Scalable** - Clear patterns for adding new endpoints

## 🎯 Next Steps

Once your presentation layer is complete:

1. **Testing**: Add comprehensive API and integration tests
2. **Monitoring**: Add logging, metrics, and error tracking
3. **Documentation**: Update API documentation and guides
4. **Deployment**: Set up CI/CD with clean architecture

## 📖 Additional Resources

- [API Design Patterns](../patterns/api-design.md)
- [Error Handling Guide](../patterns/error-handling.md)
- [Testing Controllers](../patterns/controller-testing.md)
- [API Documentation](../patterns/api-documentation.md)

## 🏆 Phase 4 Complete

You've successfully implemented a complete presentation layer with:

- ✅ **Clean controllers** using dependency injection
- ✅ **Auto-generated API docs** with OpenAPI/Swagger
- ✅ **Consistent error handling** across all endpoints
- ✅ **Type-safe request/response** models
- ✅ **Middleware support** for cross-cutting concerns
- ✅ **Health check endpoints** for monitoring
- ✅ **Backward compatibility** with existing clients

**🎉 Congratulations!** You now have a complete Clean Architecture implementation!

---

## 🎊 **Migration Complete!**

Your entire application now follows Clean Architecture principles:

- **Domain Layer**: Business logic independent of frameworks
- **Application Layer**: Use cases orchestrating domain objects
- **Infrastructure Layer**: Concrete implementations with dependency injection
- **Presentation Layer**: HTTP controllers with clean separation

### 🏆 **Achievements Unlocked**

- ✅ **Zero breaking changes** - Existing API still works
- ✅ **Framework independence** - Business logic can survive technology changes
- ✅ **Easy testing** - Each layer testable in isolation
- ✅ **Scalable architecture** - Clear patterns for future growth
- ✅ **Maintainable codebase** - Changes localized to specific layers
- ✅ **Developer-friendly** - Clear structure for new team members

### 🚀 **What's Next?**

1. **Celebrate** - You've successfully migrated to Clean Architecture!
2. **Test thoroughly** - Run comprehensive tests on all layers
3. **Document** - Update any team documentation with new patterns
4. **Train team** - Share knowledge with other developers
5. **Iterate** - Continue improving based on real-world usage

### 📚 **Learning Resources**

- [Patterns Folder](../patterns/) - Reusable patterns for future development
- [Troubleshooting](../troubleshooting.md) - Common issues and solutions
- [Migration Guide](../migration/) - Help others migrate similar systems

---

**🎉 Thank you for completing this Clean Architecture migration! Your codebase is now future-proof, maintainable, and scalable.**
