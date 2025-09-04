# Phase 2: Application Layer Implementation

## 🎯 What You'll Build

Create use cases and DTOs that orchestrate your domain objects:

- ✅ Use cases for business operations
- ✅ Data Transfer Objects (DTOs) for API contracts
- ✅ Application services for complex workflows
- ✅ Input validation and error handling
- ✅ Clear separation between HTTP concerns and business logic

## 📋 Prerequisites

- [x] [Domain Layer Phase](../phases/01-domain-layer.md) completed
- [x] Domain entities, services, and repositories implemented
- [x] Unit tests passing for domain logic
- [x] 2-3 hours available

## 🛠️ Implementation Steps

### Step 1: Create Base DTOs (10 minutes)

**Create file:** `application/dto/base_dto.py`

```python
from abc import ABC
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class BaseDTO(BaseModel):
    """Base class for all Data Transfer Objects"""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ResponseDTO(BaseDTO):
    """Base response DTO with common fields"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
```

### Step 2: Create Tenant DTOs (15 minutes)

**Create file:** `application/dto/tenant_dto.py`

```python
from typing import Optional
from datetime import datetime
from application.dto.base_dto import BaseDTO, ResponseDTO

# Request DTOs
class CreateTenantRequest(BaseDTO):
    """Request DTO for creating a tenant"""
    name: str
    organization_id: int
    is_waitlist: bool = False

class AdmitTenantRequest(BaseDTO):
    """Request DTO for admitting a tenant"""
    tenant_id: int
    admission_date: datetime

class UpdateTenantRequest(BaseDTO):
    """Request DTO for updating a tenant"""
    name: Optional[str] = None
    is_waitlist: Optional[bool] = None

# Response DTOs
class TenantResponse(ResponseDTO):
    """Response DTO for tenant data"""
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

class TenantListResponse(BaseDTO):
    """Response DTO for tenant lists"""
    tenants: list[TenantResponse]
    total_count: int

class WaitlistResponse(BaseDTO):
    """Response DTO for waitlist data"""
    waitlist: list[TenantResponse]
    total_count: int
```

### Step 3: Create User DTOs (15 minutes)

**Create file:** `application/dto/user_dto.py`

```python
from typing import Optional
from application.dto.base_dto import BaseDTO, ResponseDTO

# Request DTOs
class CreateUserRequest(BaseDTO):
    """Request DTO for creating a user"""
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UpdateUserRoleRequest(BaseDTO):
    """Request DTO for updating user role"""
    user_id: int
    new_role: str

class AuthenticateUserRequest(BaseDTO):
    """Request DTO for user authentication"""
    email: str

# Response DTOs
class UserResponse(ResponseDTO):
    """Response DTO for user data"""
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "pending"
    community_org: Optional[str] = None
    organization_id: Optional[int] = None
    
    @classmethod
    def from_entity(cls, user) -> 'UserResponse':
        """Convert domain entity to response DTO"""
        return cls(
            id=user.id,
            created_at=user.created_at,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            community_org=user.community_org,
            organization_id=user.organization_id
        )

class LoginResult(BaseDTO):
    """Response DTO for successful login"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int = 3600
```

### Step 4: Create Tenant Use Cases (20 minutes)

**Create file:** `application/use_cases/tenant_use_cases.py`

```python
from typing import List, Optional
from datetime import datetime
from application.dto.tenant_dto import (
    CreateTenantRequest, AdmitTenantRequest, UpdateTenantRequest,
    TenantResponse, TenantListResponse, WaitlistResponse
)
from domain.services.tenant_service import TenantService
from domain.entities.tenant_entity import TenantEntity
from domain.exceptions.tenant_exceptions import (
    TenantNotFoundError, TenantAlreadyExistsError, TenantAdmissionError
)

class CreateTenantUseCase:
    """Use case for creating a new tenant"""
    
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self, request: CreateTenantRequest) -> TenantResponse:
        """Execute tenant creation"""
        # Convert request to domain entity
        tenant = TenantEntity.create_tenant(
            name=request.name,
            organization_id=request.organization_id,
            is_waitlist=request.is_waitlist
        )
        
        # Execute business logic
        created_tenant = await self._tenant_service.create_tenant(tenant)
        
        # Convert to response
        return TenantResponse.from_entity(created_tenant)

class AdmitTenantUseCase:
    """Use case for admitting a tenant"""
    
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self, request: AdmitTenantRequest) -> TenantResponse:
        """Execute tenant admission"""
        # Execute business logic
        admitted_tenant = await self._tenant_service.admit_tenant(
            tenant_id=request.tenant_id,
            admission_date=request.admission_date
        )
        
        # Convert to response
        return TenantResponse.from_entity(admitted_tenant)

class GetTenantUseCase:
    """Use case for getting a tenant by ID"""
    
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self, tenant_id: int) -> Optional[TenantResponse]:
        """Execute get tenant"""
        tenant = await self._tenant_service.get_tenant(tenant_id)
        
        if tenant:
            return TenantResponse.from_entity(tenant)
        return None

class GetWaitlistTenantsUseCase:
    """Use case for getting waitlist tenants"""
    
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self, org_id: int) -> WaitlistResponse:
        """Execute get waitlist tenants"""
        waitlist_tenants = await self._tenant_service.get_waitlist_tenants(org_id)
        
        tenant_responses = [
            TenantResponse.from_entity(tenant) 
            for tenant in waitlist_tenants
        ]
        
        return WaitlistResponse(
            waitlist=tenant_responses,
            total_count=len(tenant_responses)
        )
```

### Step 5: Create User Use Cases (20 minutes)

**Create file:** `application/use_cases/user_use_cases.py`

```python
from typing import Optional
from application.dto.user_dto import (
    CreateUserRequest, UpdateUserRoleRequest, AuthenticateUserRequest,
    UserResponse, LoginResult
)
from domain.services.user_service import UserService
from domain.entities.user_entity import UserEntity
from domain.exceptions.user_exceptions import (
    UserNotFoundError, UserAlreadyExistsError, UserAuthenticationError
)

class CreateUserUseCase:
    """Use case for creating a new user"""
    
    def __init__(self, user_service: UserService):
        self._user_service = user_service
    
    async def execute(self, request: CreateUserRequest) -> UserResponse:
        """Execute user creation"""
        # Convert request to domain entity
        user = UserEntity.create_user(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name
        )
        
        # Execute business logic
        created_user = await self._user_service.create_user(user)
        
        # Convert to response
        return UserResponse.from_entity(created_user)

class AuthenticateUserUseCase:
    """Use case for authenticating a user"""
    
    def __init__(self, user_service: UserService):
        self._user_service = user_service
    
    async def execute(self, request: AuthenticateUserRequest) -> LoginResult:
        """Execute user authentication"""
        # Execute business logic
        authenticated_user = await self._user_service.authenticate_user(request.email)
        
        # Create login result (simplified - in real app you'd create JWT token)
        return LoginResult(
            access_token="mock_token",  # Would be real JWT token
            user=UserResponse.from_entity(authenticated_user)
        )

class UpdateUserRoleUseCase:
    """Use case for updating user role"""
    
    def __init__(self, user_service: UserService):
        self._user_service = user_service
    
    async def execute(self, request: UpdateUserRoleRequest) -> UserResponse:
        """Execute user role update"""
        # Execute business logic
        updated_user = await self._user_service.update_user_role(
            user_id=request.user_id,
            new_role=request.new_role
        )
        
        # Convert to response
        return UserResponse.from_entity(updated_user)

class GetUserUseCase:
    """Use case for getting a user by ID"""
    
    def __init__(self, user_service: UserService):
        self._user_service = user_service
    
    async def execute(self, user_id: int) -> Optional[UserResponse]:
        """Execute get user"""
        user = await self._user_service.get_user(user_id)
        
        if user:
            return UserResponse.from_entity(user)
        return None
```

### Step 6: Create Application Services (15 minutes)

**Create file:** `application/services/tenant_management_service.py`

```python
from typing import List
from datetime import datetime
from application.dto.tenant_dto import (
    CreateTenantRequest, AdmitTenantRequest, TenantResponse
)
from application.use_cases.tenant_use_cases import (
    CreateTenantUseCase, AdmitTenantUseCase, GetWaitlistTenantsUseCase
)

class TenantManagementService:
    """Application service for complex tenant workflows"""
    
    def __init__(self, 
                 create_tenant_use_case: CreateTenantUseCase,
                 admit_tenant_use_case: AdmitTenantUseCase,
                 get_waitlist_use_case: GetWaitlistTenantsUseCase):
        self._create_tenant_use_case = create_tenant_use_case
        self._admit_tenant_use_case = admit_tenant_use_case
        self._get_waitlist_use_case = get_waitlist_use_case
    
    async def process_tenant_admission_workflow(self, 
                                               create_request: CreateTenantRequest,
                                               admit_request: AdmitTenantRequest) -> TenantResponse:
        """Complete workflow: create tenant and admit them"""
        # Step 1: Create the tenant
        created_tenant = await self._create_tenant_use_case.execute(create_request)
        
        # Step 2: Admit the tenant (update the request with the new tenant ID)
        admit_request.tenant_id = created_tenant.id
        admitted_tenant = await self._admit_tenant_use_case.execute(admit_request)
        
        return admitted_tenant
    
    async def get_admission_ready_tenants(self, org_id: int) -> List[TenantResponse]:
        """Get tenants ready for admission (simplified business logic)"""
        waitlist_result = await self._get_waitlist_use_case.execute(org_id)
        
        # Filter tenants that can be admitted (business logic)
        admission_ready = [
            tenant for tenant in waitlist_result.waitlist
            if tenant.is_waitlist  # Additional business rules could go here
        ]
        
        return admission_ready
```

### Step 7: Create Exception Handlers (10 minutes)

**Create file:** `application/exceptions/exception_handlers.py`

```python
from fastapi import HTTPException, status
from domain.exceptions.tenant_exceptions import (
    TenantNotFoundError, TenantAlreadyExistsError, TenantAdmissionError
)
from domain.exceptions.user_exceptions import (
    UserNotFoundError, UserAlreadyExistsError, UserAuthenticationError
)

def handle_domain_exceptions(func):
    """Decorator to handle domain exceptions and convert to HTTP exceptions"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TenantNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        except TenantAlreadyExistsError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        except TenantAdmissionError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        except UserAlreadyExistsError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        except UserAuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    return wrapper
```

## ✅ Success Criteria

- [ ] `application/dto/` directory created with base DTOs
- [ ] `application/dto/tenant_dto.py` with all tenant DTOs
- [ ] `application/dto/user_dto.py` with all user DTOs
- [ ] `application/use_cases/tenant_use_cases.py` with tenant use cases
- [ ] `application/use_cases/user_use_cases.py` with user use cases
- [ ] `application/services/tenant_management_service.py` with workflow logic
- [ ] `application/exceptions/exception_handlers.py` with error handling
- [ ] Unit tests for use cases and DTOs
- [ ] Integration tests for complete workflows

## 🧪 Testing Your Implementation

```bash
# Test application layer
pytest tests/application/ -v

# Test use cases specifically
pytest tests/application/use_cases/ -v

# Test DTOs
pytest tests/application/dto/ -v
```

## 🆘 Common Issues & Solutions

### Issue: Pydantic Import Errors

ImportError: cannot import name 'BaseModel' from 'pydantic'

**Solution:** Ensure pydantic is installed and imported correctly:

```bash
pip install pydantic
```

### Issue: DTO Validation Errors

- Check that all required fields are provided
- Verify data types match between DTOs and domain entities
- Ensure datetime fields are properly formatted

### Issue: Use Case Dependencies

- Make sure domain services are properly injected
- Check that repository interfaces are correctly implemented
- Verify dependency injection container is configured

### Issue: Exception Handling Not Working

- Ensure exception handlers are applied to controller methods
- Check that domain exceptions are being raised correctly
- Verify HTTP status codes are appropriate

## 📚 What You've Accomplished

### Before (Current Architecture)

```python
# Controller directly handles business logic
@tenant_router.post('/create-tenant')
def create_tenant(request: TenantCreateRequest, db: Session):
    # Business logic mixed with HTTP concerns
    if not tenant_dao.exists_by_name(request.name, db):
        tenant = Tenant(name=request.name, org_id=request.org_id)
        db.add(tenant)
        db.commit()
        return {"tenant": tenant}
    else:
        raise HTTPException(409, "Tenant already exists")
```

### After (Clean Architecture)

```python
# Controller delegates to use case
@tenant_router.post('/create-tenant')
@handle_domain_exceptions
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
):
    # HTTP concerns separated from business logic
    return await use_case.execute(request)

# Use case handles business logic
class CreateTenantUseCase:
    async def execute(self, request: CreateTenantRequest) -> TenantResponse:
        tenant = TenantEntity.create_tenant(request.name, request.organization_id)
        created_tenant = await self._tenant_service.create_tenant(tenant)
        return TenantResponse.from_entity(created_tenant)
```

## 🔄 Integration with Existing Code

### Option 1: New Endpoints (Recommended)

Create new API endpoints using clean architecture while keeping old ones:

```python
# New clean architecture endpoints
@tenant_router.post('/v2/tenants')
async def create_tenant_v2(request: CreateTenantRequest):
    # Uses clean architecture

# Legacy endpoints (keep working)
@tenant_router.post('/tenants')
def create_tenant_v1(request: dict, db: Session):
    # Uses existing DAO logic
```

### Option 2: Feature Flags

```python
USE_CLEAN_ARCHITECTURE = os.getenv('USE_CLEAN_ARCHITECTURE', 'false').lower() == 'true'

@tenant_router.post('/tenants')
async def create_tenant(request):
    if USE_CLEAN_ARCHITECTURE:
        # Use new use case
        return await create_tenant_use_case.execute(request)
    else:
        # Use existing logic
        return create_tenant_dao_logic(request)
```

## 📈 Benefits Achieved

### Developer Experience

- ✅ **Clear API contracts** - DTOs define exactly what data is expected
- ✅ **Testable workflows** - Use cases can be tested independently
- ✅ **Consistent error handling** - Centralized exception management
- ✅ **Framework independence** - Business logic separate from HTTP concerns

### Code Quality

- ✅ **Single responsibility** - Each use case does one thing
- ✅ **Dependency inversion** - Controllers depend on abstractions
- ✅ **Validation at boundaries** - Input validation in DTOs
- ✅ **Rich error responses** - Meaningful error messages

### Business Value

- ✅ **Easier API evolution** - Change internal logic without affecting API
- ✅ **Better client experience** - Consistent response formats
- ✅ **Scalable architecture** - Clear patterns for adding new features
- ✅ **Maintainable codebase** - Changes localized to specific use cases

## 🎯 Next Steps

Once your application layer is complete:

1. **Infrastructure Layer**: Implement repository concrete classes
2. **Dependency Injection**: Wire up all dependencies
3. **Presentation Layer**: Create controllers (optional)
4. **Testing**: Add integration tests

## 📖 Additional Resources

- [DTO Pattern Explained](../patterns/dtos.md)
- [Use Case Pattern Guide](../patterns/use-cases.md)
- [Testing Application Layer](../patterns/testing.md)
- [Infrastructure Layer Guide](../phases/03-infrastructure-layer.md)

## 🏆 Phase 2 Complete

You've successfully implemented a complete application layer with:

- ✅ **Use cases** for business operations
- ✅ **DTOs** for clear API contracts
- ✅ **Application services** for complex workflows
- ✅ **Exception handling** for consistent error responses
- ✅ **Comprehensive tests** ensuring correctness
- ✅ **Clean separation** between HTTP and business logic

**🎉 Congratulations!** Your application layer now orchestrates domain objects while keeping HTTP concerns separate.

---

**Ready for Phase 3?** → [Infrastructure Layer Guide](03-infrastructure-layer.md)
