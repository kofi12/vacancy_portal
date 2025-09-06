# 📋 Chronological Clean Architecture Implementation Plan

## Current State Analysis

**✅ Already Implemented:**

- Basic domain entities (TenantEntity with business logic)
- Database models and schemas
- Traditional DAO layer
- FastAPI controllers

**❌ Missing Components:**

- Domain services and repository implementations
- Use cases and application layer
- Clean Architecture dependency injection
- Updated controllers

---

## 🏗️ Deep Dive: Understanding Clean Architecture Layers

### What Problems Does Clean Architecture Solve?

**🔴 The Traditional Problem:**

```python
# Traditional approach (tightly coupled)
@tenant_router.post('/create-tenant')
def create_tenant(data: dict, db: Session):
    # Controller directly calls DAO
    tenant = tenant_dao.create_tenant(data, db)
    # Business logic scattered across files
    if tenant.waitlist:
        tenant.admission_date = datetime.now()
    return tenant
```

**🟢 Clean Architecture Solution:**

```python
# Clean approach (layers separated)
@tenant_router.post('/create-tenant')
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
):
    return await use_case.execute(request)
```

**Key Problems Solved:**

1. **Framework Lock-in** - Business logic depends on FastAPI/SQLAlchemy
2. **Testing Difficulties** - Can't test business logic without database
3. **Code Scattering** - Business rules spread across controllers and DAOs
4. **Change Resistance** - Database changes break business logic
5. **Poor Maintainability** - Hard to find and modify related code

### How Layers Interact

**Dependency Flow:**

```mermaid
Presentation Layer → Application Layer → Domain Layer ← Infrastructure Layer
       ↓                     ↓                     ↑             ↑
    HTTP/JSON             Use Cases         Business Rules   Database/API
```

**Interaction Patterns:**

1. **Presentation → Application**: Controllers pass validated input to use cases
2. **Application → Domain**: Use cases orchestrate domain objects and services
3. **Domain → Infrastructure**: Domain defines interfaces, infrastructure implements them
4. **Infrastructure → Domain**: Repository implementations return domain entities

**Communication Style:**

- **Inner layers don't know about outer layers** (Domain doesn't import FastAPI)
- **Outer layers depend on inner layers** (Controllers import domain entities)
- **Data flows inward, control flows outward**

---

## 🐍 Python Best Practices for Clean Architecture

### 1. Type Hints & Data Classes

```python
from dataclasses import dataclass
from typing import Optional, List
from abc import ABC, abstractmethod

@dataclass(frozen=True)  # Immutable data
class CreateTenantRequest:
    name: str
    organization_id: int

class TenantRepository(ABC):
    @abstractmethod
    async def get_by_id(self, tenant_id: int) -> Optional[TenantEntity]:
        pass
```

**Why?**

- **Type Safety**: Catch errors at development time
- **Documentation**: Types serve as living documentation
- **IDE Support**: Better autocomplete and refactoring
- **Runtime Introspection**: Useful for validation and serialization

### 2. Dependency Injection with Protocols

```python
from typing import Protocol

class TenantRepositoryProtocol(Protocol):
    async def get_by_id(self, tenant_id: int) -> Optional[TenantEntity]: ...

class TenantService:
    def __init__(self, tenant_repo: TenantRepositoryProtocol):
        self._tenant_repo = tenant_repo
```

**Why?**

- **Testability**: Easy to mock dependencies
- **Flexibility**: Can swap implementations without changing code
- **Explicit Dependencies**: Clear what each class needs

### 3. Factory Methods for Entity Creation

```python
@dataclass
class TenantEntity(BaseEntity):
    _name: str
    _organization_id: int
    _is_waitlist: bool = True

    @classmethod
    def create_tenant(cls, name: str, organization_id: int) -> 'TenantEntity':
        """Factory method with validation"""
        if not name or not name.strip():
            raise ValueError("Tenant name cannot be empty")
        if organization_id <= 0:
            raise ValueError("Valid organization ID required")

        return cls(
            _name=name.strip(),
            _organization_id=organization_id,
            _is_waitlist=True
        )
```

**Why?**

- **Encapsulation**: Hide complex construction logic
- **Validation**: Centralize input validation
- **Immutability**: Prevent invalid object states
- **Testability**: Easy to create test instances

### 4. Context Managers for Resource Management

```python
class SQLTenantRepository(TenantRepository):
    def __init__(self, session_factory: Callable[[], Session]):
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: int) -> Optional[TenantEntity]:
        async with self._session_factory() as session:
            stmt = select(TenantModel).where(TenantModel.id == tenant_id)
            result = await session.execute(stmt)
            return self._to_entity(result.scalar_one_or_none())
```

**Why?**

- **Resource Safety**: Automatic cleanup
- **Exception Safety**: Resources cleaned up even if errors occur
- **Thread Safety**: Each operation gets its own session

### 5. Result Types for Error Handling

```python
from typing import Union

@dataclass
class Success:
    value: Any

@dataclass
class Failure:
    error: Exception

Result = Union[Success, Failure]

class TenantService:
    async def admit_tenant(self, tenant_id: int) -> Result:
        try:
            tenant = await self._tenant_repo.get_by_id(tenant_id)
            if not tenant:
                return Failure(TenantNotFoundError(f"Tenant {tenant_id} not found"))

            tenant.admit()
            saved = await self._tenant_repo.update(tenant)
            return Success(saved)
        except Exception as e:
            return Failure(e)
```

**Why?**

- **Explicit Error Handling**: No silent failures
- **Type Safety**: Compiler catches unhandled error cases
- **Composability**: Easy to chain operations
- **Testability**: Clear success/failure paths

---

## ⚠️ Common Pitfalls to Avoid

### 1. Anemic Domain Model

**❌ Wrong:**

```python
class TenantEntity:
    def __init__(self, name: str, organization_id: int):
        self.name = name
        self.organization_id = organization_id
        # No business logic - just data
```

**✅ Right:**

```python
class TenantEntity:
    def __init__(self, name: str, organization_id: int):
        self._name = name
        self._organization_id = organization_id

    def can_be_admitted(self) -> bool:
        """Business rule: only waitlist tenants can be admitted"""
        return self._is_waitlist

    def admit(self) -> None:
        """Business logic with validation"""
        if not self.can_be_admitted():
            raise ValueError("Cannot admit non-waitlist tenant")
        self._admission_date = datetime.now()
        self._is_waitlist = False
```

### 2. Fat Controllers

**❌ Wrong:**

```python
@tenant_router.post('/create-tenant')
def create_tenant(request: TenantBase, db: Session):
    # Controller doing business logic
    if request.organization_id not in [1, 2, 3]:
        raise HTTPException(400, "Invalid organization")

    tenant = Tenant(name=request.name, organization_id=request.organization_id)
    db.add(tenant)
    db.commit()
    return tenant
```

**✅ Right:**

```python
@tenant_router.post('/create-tenant')
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
):
    try:
        result = await use_case.execute(request)
        return TenantResponse.from_entity(result.tenant)
    except DomainException as e:
        raise HTTPException(400, str(e))
```

### 3. Repository Pattern Violations

**❌ Wrong:**

```python
class SQLTenantRepository:
    def get_active_tenants_by_org(self, org_id: int):
        # Business logic in repository
        return self._session.query(Tenant).filter(
            Tenant.organization_id == org_id,
            Tenant.waitlist == False,
            Tenant.discharge_date.is_(None)
        ).all()
```

**✅ Right:**

```python
class SQLTenantRepository:
    async def get_by_organization(self, org_id: int) -> List[TenantEntity]:
        # Just data access
        stmt = select(Tenant).where(Tenant.organization_id == org_id)
        results = await self._session.execute(stmt)
        return [self._to_entity(r) for r in results]
```

### 4. Cross-Layer Dependencies

**❌ Wrong:**

```python
# Domain layer importing FastAPI
from fastapi import HTTPException

class TenantService:
    def admit_tenant(self, tenant_id: int):
        if not self._repo.exists(tenant_id):
            raise HTTPException(404, "Tenant not found")  # Wrong layer!
```

**✅ Right:**

```python
# Domain layer defines its own exceptions
class TenantNotFoundError(ValueError):
    pass

class TenantService:
    async def admit_tenant(self, tenant_id: int) -> TenantEntity:
        tenant = await self._repo.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")
        # Controller handles HTTP translation
```

### 5. God Classes

**❌ Wrong:**

```python
class TenantManager:  # Does everything!
    def __init__(self, db: Session):
        self.db = db

    def create_tenant(self, data):
        # Validation, persistence, business logic all mixed
        pass

    def admit_tenant(self, tenant_id):
        pass

    def get_tenant(self, tenant_id):
        pass
```

**✅ Right:**

```python
# Separate concerns
class TenantService:  # Business logic
    def admit_tenant(self, tenant_id: int):
        pass

class CreateTenantUseCase:  # Application logic
    def execute(self, request):
        pass

class SQLTenantRepository:  # Data access
    def get_by_id(self, tenant_id: int):
        pass
```

---

## 📚 Detailed Layer Explanations

### 🎯 Domain Layer Deep Dive

**What it is:** The heart of your application - pure business logic with zero external dependencies.

**Why it exists:**

- **Framework Independence**: Business rules don't depend on web frameworks, databases, or external APIs
- **Testability**: Can test business logic in isolation without setting up databases or HTTP servers
- **Reusability**: Same business logic can work in web apps, CLI tools, or background jobs
- **Stability**: Business rules change less frequently than technology choices

**Key Characteristics:**

- **No imports** from FastAPI, SQLAlchemy, or external libraries
- **Rich domain models** with business logic methods
- **Value objects** for immutable concepts
- **Domain events** for cross-entity communication
- **Business exceptions** that make sense to domain experts

**Example Domain Entity:**

```python
@dataclass
class TenantEntity(BaseEntity):
    _name: str
    _organization_id: int
    _admission_date: Optional[datetime] = None
    _is_waitlist: bool = True

    @classmethod
    def create_tenant(cls, name: str, organization_id: int) -> 'TenantEntity':
        """Factory method ensuring valid tenant creation"""
        if not name or not name.strip():
            raise TenantValidationError("Tenant name cannot be empty")
        if organization_id <= 0:
            raise TenantValidationError("Valid organization ID required")

        return cls(
            _name=name.strip(),
            _organization_id=organization_id,
            _is_waitlist=True
        )

    def can_be_admitted(self) -> bool:
        """Business rule: only waitlist tenants can be admitted"""
        return self._is_waitlist and self._admission_date is None

    def admit(self) -> None:
        """Business logic for tenant admission"""
        if not self.can_be_admitted():
            raise TenantAdmissionError("Tenant is not eligible for admission")

        self._admission_date = datetime.now()
        self._is_waitlist = False

    def discharge(self, discharge_date: datetime) -> None:
        """Business logic for tenant discharge"""
        if self._admission_date is None:
            raise TenantDischargeError("Cannot discharge tenant who was never admitted")

        if discharge_date < self._admission_date:
            raise TenantDischargeError("Discharge date cannot be before admission date")

        self._discharge_date = discharge_date
```

### ⚙️ Application Layer Deep Dive

**What it is:** Orchestrates domain objects to fulfill user requests and application workflows.

**Why it exists:**

- **Use Case Coordination**: Handles complex interactions between multiple domain objects
- **Input/Output Transformation**: Converts between external formats and domain objects
- **Application Logic**: Rules specific to how the application should behave
- **Transaction Management**: Ensures data consistency across operations

**Key Characteristics:**

- **Use Cases**: Specific application operations (CreateTenant, AdmitTenant, GenerateReport)
- **DTOs**: Data Transfer Objects for request/response structures
- **Application Services**: Handle cross-cutting concerns within the application layer
- **Input Validation**: Application-level validation (not just domain constraints)

**Example Use Case:**

```python
@dataclass(frozen=True)
class AdmitTenantRequest:
    tenant_id: int
    admission_date: Optional[datetime] = None

@dataclass(frozen=True)
class AdmitTenantResponse:
    tenant: TenantEntity
    was_waitlisted: bool

class AdmitTenantUseCase:
    """Application use case for admitting a tenant"""

    def __init__(
        self,
        tenant_service: TenantService,
        organization_service: OrganizationService
    ):
        self._tenant_service = tenant_service
        self._organization_service = organization_service

    async def execute(self, request: AdmitTenantRequest) -> AdmitTenantResponse:
        # 1. Validate organization exists and has capacity
        org = await self._organization_service.get_by_id(request.tenant.organization_id)
        if not org:
            raise OrganizationNotFoundError(f"Organization {request.tenant.organization_id} not found")

        if not org.has_available_beds():
            raise OrganizationCapacityError("Organization has no available beds")

        # 2. Get tenant and validate admission eligibility
        tenant = await self._tenant_service.get_tenant(request.tenant_id)
        was_waitlisted = tenant.is_waitlist

        # 3. Admit the tenant (domain logic)
        admitted_tenant = await self._tenant_service.admit_tenant(
            request.tenant_id,
            request.admission_date
        )

        # 4. Update organization capacity
        await self._organization_service.decrement_available_beds(org.id)

        return AdmitTenantResponse(
            tenant=admitted_tenant,
            was_waitlisted=was_waitlisted
        )
```

### 🔧 Infrastructure Layer Deep Dive

**What it is:** Implements domain interfaces and handles external concerns (database, APIs, file systems).

**Why it exists:**

- **Technology Abstraction**: Domain doesn't need to know about specific databases or APIs
- **Implementation Flexibility**: Can swap PostgreSQL for MongoDB without changing business logic
- **External Service Integration**: Handles communication with payment processors, email services, etc.
- **Resource Management**: Manages connections, sessions, and external resources

**Key Characteristics:**

- **Repository Implementations**: Concrete database access classes
- **External API Clients**: Wrappers for third-party services
- **File System Operations**: Document storage, uploads, downloads
- **Authentication Services**: OAuth, JWT implementations
- **Email/SMS Services**: Notification delivery mechanisms

**Example Repository Implementation:**

```python
class SQLTenantRepository(TenantRepository):
    """SQLAlchemy implementation of TenantRepository"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory

    async def create(self, tenant: TenantEntity) -> TenantEntity:
        async with self._session_factory() as session:
            # Convert domain entity to database model
            db_tenant = Tenant(
                name=tenant.name,
                organization_id=tenant.organization_id,
                waitlist=tenant.is_waitlist,
                admission_date=tenant.admission_date,
                discharge_date=tenant.discharge_date
            )

            session.add(db_tenant)
            await session.commit()
            await session.refresh(db_tenant)

            # Convert back to domain entity
            return self._to_entity(db_tenant)

    async def get_by_id(self, tenant_id: int) -> Optional[TenantEntity]:
        async with self._session_factory() as session:
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
            db_tenant = result.scalar_one_or_none()
            return self._to_entity(db_tenant) if db_tenant else None

    async def update(self, tenant: TenantEntity) -> TenantEntity:
        async with self._session_factory() as session:
            # Update existing record
            stmt = (
                update(Tenant)
                .where(Tenant.id == tenant.id)
                .values(
                    name=tenant.name,
                    waitlist=tenant.is_waitlist,
                    admission_date=tenant.admission_date,
                    discharge_date=tenant.discharge_date
                )
            )
            await session.execute(stmt)
            await session.commit()

            # Return updated entity
            return await self.get_by_id(tenant.id)  # type: ignore

    def _to_entity(self, db_tenant: Tenant) -> TenantEntity:
        """Convert database model to domain entity"""
        return TenantEntity(
            id=db_tenant.id,
            name=db_tenant.name,
            organization_id=db_tenant.organization_id,
            admission_date=db_tenant.admission_date,
            discharge_date=db_tenant.discharge_date,
            is_waitlist=db_tenant.waitlist,
            created_at=db_tenant.created_at
        )
```

### 🌐 Presentation Layer Deep Dive

**What it is:** Handles HTTP requests, formats responses, and manages web framework concerns.

**Why it exists:**

- **HTTP Protocol Handling**: Request parsing, response formatting, status codes
- **Web Framework Integration**: FastAPI routes, middleware, dependency injection
- **API Documentation**: OpenAPI/Swagger generation
- **Cross-cutting Concerns**: Authentication, logging, rate limiting, CORS

**Key Characteristics:**

- **Thin Controllers**: Minimal logic, delegate to use cases
- **Request/Response Models**: API-specific serialization
- **Middleware**: Authentication, logging, error handling
- **Input Validation**: API-level validation using Pydantic
- **Error Translation**: Convert domain exceptions to HTTP responses

**Example Clean Controller:**

```python
@tenant_router.post(
    '/admit-tenant',
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Admit a tenant from waitlist",
    responses={
        200: {"description": "Tenant successfully admitted"},
        400: {"description": "Invalid request data"},
        404: {"description": "Tenant or organization not found"},
        409: {"description": "Organization has no available beds"}
    }
)
async def admit_tenant(
    request: AdmitTenantRequest,
    admit_use_case: AdmitTenantUseCase = Depends(get_admit_tenant_use_case),
    current_user: User = Depends(get_current_user)
) -> TenantResponse:
    """
    Admit a tenant from the waitlist to an available bed.

    - **tenant_id**: ID of the tenant to admit
    - **admission_date**: Optional admission date (defaults to now)

    Requires write permissions for tenants.
    """
    try:
        result = await admit_use_case.execute(request)
        return TenantResponse.from_entity(result.tenant)

    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID {request.tenant_id} not found"
        )
    except OrganizationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except OrganizationCapacityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization has no available beds"
        )
    except TenantAdmissionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

---

## 🧪 Testing Strategies by Layer

### Domain Layer Testing

```python
# domain/entities/tests/test_tenant_entity.py
import pytest
from datetime import datetime
from domain.entities.tenant_entity import TenantEntity
from domain.exceptions.tenant_exceptions import TenantAdmissionError

class TestTenantEntity:
    def test_create_tenant_with_valid_data(self):
        tenant = TenantEntity.create_tenant("John Doe", 1)

        assert tenant.name == "John Doe"
        assert tenant.organization_id == 1
        assert tenant.is_waitlist == True
        assert tenant.admission_date is None

    def test_create_tenant_with_empty_name_raises_error(self):
        with pytest.raises(ValueError, match="Tenant name cannot be empty"):
            TenantEntity.create_tenant("", 1)

    def test_can_be_admitted_only_if_waitlist_and_no_admission_date(self):
        # Waitlist tenant with no admission date - can be admitted
        tenant = TenantEntity.create_tenant("John", 1)
        assert tenant.can_be_admitted() == True

        # Admit the tenant
        tenant.admit()

        # Now cannot be admitted again
        assert tenant.can_be_admitted() == False

    def test_admit_tenant_success(self):
        tenant = TenantEntity.create_tenant("John", 1)
        tenant.admit()

        assert tenant.is_waitlist == False
        assert tenant.admission_date is not None

    def test_admit_non_waitlist_tenant_raises_error(self):
        tenant = TenantEntity.create_tenant("John", 1)
        tenant.admit()  # First admission succeeds

        # Second admission should fail
        with pytest.raises(TenantAdmissionError):
            tenant.admit()
```

### Application Layer Testing

```python
# application/use_cases/tests/test_admit_tenant.py
import pytest
from unittest.mock import AsyncMock
from application.use_cases.admit_tenant import AdmitTenantUseCase, AdmitTenantRequest
from domain.exceptions.tenant_exceptions import TenantNotFoundError

class TestAdmitTenantUseCase:
    @pytest.fixture
    def tenant_service_mock(self):
        return AsyncMock()

    @pytest.fixture
    def organization_service_mock(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, tenant_service_mock, organization_service_mock):
        return AdmitTenantUseCase(tenant_service_mock, organization_service_mock)

    @pytest.mark.asyncio
    async def test_admit_tenant_success(self, use_case, tenant_service_mock, organization_service_mock):
        # Arrange
        request = AdmitTenantRequest(tenant_id=1)
        mock_tenant = AsyncMock()
        mock_org = AsyncMock()
        mock_org.has_available_beds.return_value = True

        tenant_service_mock.get_tenant.return_value = mock_tenant
        organization_service_mock.get_by_id.return_value = mock_org
        tenant_service_mock.admit_tenant.return_value = mock_tenant

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result.tenant == mock_tenant
        assert result.was_waitlisted == mock_tenant.is_waitlist
        tenant_service_mock.admit_tenant.assert_called_once_with(1, None)
        organization_service_mock.decrement_available_beds.assert_called_once()

    @pytest.mark.asyncio
    async def test_admit_tenant_not_found_raises_error(self, use_case, tenant_service_mock):
        # Arrange
        request = AdmitTenantRequest(tenant_id=999)
        tenant_service_mock.get_tenant.side_effect = TenantNotFoundError("Tenant not found")

        # Act & Assert
        with pytest.raises(TenantNotFoundError):
            await use_case.execute(request)
```

### Infrastructure Layer Testing

```python
# infrastructure/repositories/tests/test_tenant_repository.py
import pytest
from unittest.mock import AsyncMock
from infrastructure.repositories.tenant_repository_impl import SQLTenantRepository

class TestSQLTenantRepository:
    @pytest.fixture
    def session_mock(self):
        return AsyncMock()

    @pytest.fixture
    def session_factory_mock(self, session_mock):
        factory = AsyncMock()
        factory.return_value.__aenter__ = AsyncMock(return_value=session_mock)
        factory.return_value.__aexit__ = AsyncMock(return_value=None)
        return factory

    @pytest.fixture
    def repo(self, session_factory_mock):
        return SQLTenantRepository(session_factory_mock)

    @pytest.mark.asyncio
    async def test_get_by_id_returns_tenant_when_exists(self, repo, session_mock):
        # Arrange
        db_tenant = AsyncMock()
        db_tenant.id = 1
        db_tenant.name = "John Doe"

        session_mock.execute.return_value.scalar_one_or_none.return_value = db_tenant

        # Act
        result = await repo.get_by_id(1)

        # Assert
        assert result is not None
        assert result.name == "John Doe"
        session_mock.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_exists(self, repo, session_mock):
        # Arrange
        session_mock.execute.return_value.scalar_one_or_none.return_value = None

        # Act
        result = await repo.get_by_id(999)

        # Assert
        assert result is None
```

## 🐍 Additional Python Best Practices

### 6. Property-Based Testing with Hypothesis

```python
# domain/entities/tests/test_tenant_entity_property.py
import pytest
from hypothesis import given, strategies as st
from domain.entities.tenant_entity import TenantEntity

class TestTenantEntityProperties:
    @given(name=st.text(min_size=1, max_size=100))
    def test_tenant_creation_with_any_valid_name(self, name):
        """Property: Any non-empty name should create a valid tenant"""
        tenant = TenantEntity.create_tenant(name, 1)
        assert tenant.name == name.strip()
        assert tenant.organization_id == 1

    @given(org_id=st.integers(min_value=1, max_value=1000))
    def test_tenant_creation_with_any_valid_org_id(self, org_id):
        """Property: Any positive org_id should work"""
        tenant = TenantEntity.create_tenant("John", org_id)
        assert tenant.organization_id == org_id
```

### 7. Custom Base Classes for Common Behavior

```python
# domain/entities/base_entity.py
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class BaseEntity(ABC):
    """Enhanced base entity with common domain behaviors"""

    id: Optional[int] = field(default=None)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = field(default=None)

    def mark_as_updated(self) -> None:
        """Mark entity as having been updated"""
        self.updated_at = datetime.now()

    def is_new(self) -> bool:
        """Check if entity is newly created (not yet persisted)"""
        return self.id is None

    def __post_init__(self):
        """Ensure created_at is set for new entities"""
        if self.is_new():
            self.created_at = datetime.now()

# Usage in entities
@dataclass
class TenantEntity(BaseEntity):
    _name: str
    _organization_id: int
    _admission_date: Optional[datetime] = None
    _is_waitlist: bool = True

    def admit(self) -> None:
        if not self.can_be_admitted():
            raise TenantAdmissionError("Cannot admit tenant")

        self._admission_date = datetime.now()
        self._is_waitlist = False
        self.mark_as_updated()  # Track when entity was modified
```

### 8. Dependency Injection with Context Variables

```python
# infrastructure/context.py
import contextvars
from typing import Optional
from domain.repositories.tenant_repository import TenantRepository

# Context variables for dependency injection
_tenant_repo: contextvars.ContextVar[Optional[TenantRepository]] = contextvars.ContextVar(
    'tenant_repo', default=None
)

def get_tenant_repository() -> TenantRepository:
    """Get tenant repository from context"""
    repo = _tenant_repo.get()
    if repo is None:
        raise RuntimeError("Tenant repository not set in context")
    return repo

def set_tenant_repository(repo: TenantRepository) -> None:
    """Set tenant repository in context (for testing)"""
    _tenant_repo.set(repo)

# Usage in tests
def test_tenant_service_with_context():
    # Create mock repository
    mock_repo = AsyncMock()

    # Set in context
    set_tenant_repository(mock_repo)

    # Service automatically gets repository from context
    service = TenantService()

    # Test...
```

### 9. Structured Logging

```python
# domain/services/tenant_service.py
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TenantService:
    def __init__(self, tenant_repo: TenantRepository):
        self._tenant_repo = tenant_repo

    async def admit_tenant(self, tenant_id: int) -> TenantEntity:
        logger.info("Admitting tenant", extra={
            "tenant_id": tenant_id,
            "operation": "admit_tenant"
        })

        tenant = await self._tenant_repo.get_by_id(tenant_id)
        if not tenant:
            logger.warning("Tenant not found for admission", extra={
                "tenant_id": tenant_id,
                "error": "tenant_not_found"
            })
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")

        logger.info("Tenant admission validation passed", extra={
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "was_waitlist": tenant.is_waitlist
        })

        tenant.admit()
        saved = await self._tenant_repo.update(tenant)

        logger.info("Tenant successfully admitted", extra={
            "tenant_id": tenant_id,
            "admission_date": saved.admission_date.isoformat()
        })

        return saved
```

### 10. Configuration Management

```python
# infrastructure/config.py
from pydantic import BaseSettings, Field
from typing import Optional

class DatabaseConfig(BaseSettings):
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(default="vacancy_portal", env="DB_NAME")
    user: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="", env="DB_PASSWORD")

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class AppConfig(BaseSettings):
    debug: bool = Field(default=False, env="DEBUG")
    database: DatabaseConfig = DatabaseConfig()

    class Config:
        env_nested_delimiter = "__"

# Usage
config = AppConfig()
print(f"Database URL: {config.database.url}")
```

---

## Phase 1: Complete Domain Layer (No Dependencies)

### 1.1 Domain Exceptions

```mermaid
domain/exceptions/
├── __init__.py
├── tenant_exceptions.py
├── organization_exceptions.py
└── user_exceptions.py
```

**Key Concept:** Domain exceptions encapsulate business rule violations. Create these first since they have zero dependencies.

```python
# domain/exceptions/tenant_exceptions.py
class TenantNotFoundError(Exception):
    """Raised when tenant doesn't exist"""
    pass

class TenantAdmissionError(Exception):
    """Raised when tenant admission violates business rules"""
    pass
```

### 1.2 Complete Domain Entities

- Fix BaseEntity constructor (there's a bug with created_at)
- Complete OrganizationEntity and UserEntity
- Add factory methods and business logic

```python
# domain/entities/organization_entity.py
@dataclass
class OrganizationEntity(BaseEntity):
    _business_name: str
    _address: str
    _number_of_beds: int | None

    @classmethod
    def create_organization(cls, business_name: str, address: str):
        # validation logic here
        pass
```

### 1.3 Repository Interfaces

- OrganizationRepository
- UserRepository
- Add any missing methods to TenantRepository

```python
# domain/repositories/organization_repository.py
class OrganizationRepository(ABC):
    @abstractmethod
    async def create(self, org: OrganizationEntity) -> OrganizationEntity:
        pass

    @abstractmethod
    async def get_by_id(self, id: int) -> OrganizationEntity | None:
        pass
```

---

## Phase 2: Domain Services (Depends on Domain Layer)

### 2.1 Domain Services

```mermaid
domain/services/
├── tenant_service.py
├── organization_service.py
└── user_service.py
```

**Key Concept:** Domain services contain business logic that spans multiple entities or requires coordination.

```python
# domain/services/tenant_service.py
class TenantService:
    def __init__(self, tenant_repo: TenantRepository):
        self._tenant_repo = tenant_repo

    async def admit_tenant(self, tenant_id: int) -> TenantEntity:
        tenant = await self._tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")

        tenant.admit()
        return await self._tenant_repo.update(tenant)
```

---

## Phase 3: Infrastructure Layer (Depends on Domain + Database)

### 3.1 Repository Implementations

```mermaid
database/repositories/
├── __init__.py
├── tenant_repository_impl.py
├── organization_repository_impl.py
└── user_repository_impl.py
```

**Key Concept:** Infrastructure implements domain interfaces. This layer handles database operations.

```python
# database/repositories/tenant_repository_impl.py
class SQLTenantRepository(TenantRepository):
    def __init__(self, session: Session):
        self._session = session

    async def get_by_id(self, tenant_id: int) -> TenantEntity | None:
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = self._session.exec(stmt).first()
        return self._to_entity(result) if result else None

    def _to_entity(self, model: Tenant | None) -> TenantEntity | None:
        if not model:
            return None
        # Convert SQLModel to domain entity
        pass
```

### 3.2 Dependency Injection Container

```mermaid
infrastructure/
├── __init__.py
├── container.py
└── providers.py
```

**Key Concept:** Centralizes dependency creation and injection.

```python
# infrastructure/container.py
from database.repositories.tenant_repository_impl import SQLTenantRepository
from domain.services.tenant_service import TenantService

def get_tenant_service(session: Session = Depends(get_session)) -> TenantService:
    repo = SQLTenantRepository(session)
    return TenantService(repo)
```

---

## Phase 4: Application Layer (Depends on Domain + Infrastructure)

### 4.1 Use Cases

```mermaid
application/
├── __init__.py
├── use_cases/
│   ├── __init__.py
│   ├── create_tenant.py
│   ├── admit_tenant.py
│   ├── get_tenant.py
│   └── tenant_dto.py
└── services/
    └── __init__.py
```

**Key Concept:** Use cases orchestrate domain objects and handle application logic.

```python
# application/use_cases/create_tenant.py
@dataclass
class CreateTenantRequest:
    name: str
    organization_id: int

@dataclass
class CreateTenantResponse:
    tenant: TenantEntity

class CreateTenantUseCase:
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service

    async def execute(self, request: CreateTenantRequest) -> CreateTenantResponse:
        tenant = TenantEntity.create_tenant(request.name, request.organization_id)
        created_tenant = await self._tenant_service.create_tenant(tenant)
        return CreateTenantResponse(tenant=created_tenant)
```

### 4.2 Application Services

- Input validation
- Cross-cutting concerns
- Use case orchestration

---

## Phase 5: Presentation Layer (Depends on All Layers)

### 5.1 Updated Controllers

```mermaid
controller/
├── tenant_controller_v2.py  # New Clean Architecture controller
├── organization_controller_v2.py
└── user_controller_v2.py
```

**Key Concept:** Controllers are thin adapters that handle HTTP concerns and delegate to use cases.

```python
# controller/tenant_controller_v2.py
@tenant_router.post('/create-tenant')
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
) -> TenantResponse:
    result = await use_case.execute(request)
    return TenantResponse.from_entity(result.tenant)
```

### 5.2 API Schemas

```mermaid
models/
├── request_schemas.py  # Use case input DTOs
└── response_schemas.py  # Use case output DTOs
```

---

## 🎯 Implementation Strategy

### Week 1: Domain Foundation

- Fix BaseEntity
- Complete all domain entities
- Implement domain exceptions
- Create all repository interfaces

### Week 2: Business Logic

- Implement domain services
- Add comprehensive business logic
- Write domain layer unit tests

### Week 3: Data Access

- Implement repository classes
- Set up dependency injection
- Test repository implementations

### Week 4: Application Layer

- Create use cases
- Implement DTOs
- Add use case tests

### Week 5: Presentation Layer

- Update controllers
- Migrate existing endpoints
- Integration testing

---

## 🔧 Key Patterns to Follow

### 1. Dependency Inversion

Domain defines interfaces, infrastructure implements them

### 2. Single Responsibility

Each class has one reason to change

### 3. Factory Methods

Use entity factory methods for validation

### 4. Repository Pattern

Abstract data access behind interfaces

### 5. Use Case Pattern

Orchestrate domain objects for specific operations

---

## ✅ Success Criteria

- **Phase 1 Complete**: All domain entities implement business rules
- **Phase 2 Complete**: Domain services handle cross-entity logic
- **Phase 3 Complete**: Repository implementations work with existing database
- **Phase 4 Complete**: Use cases orchestrate domain operations
- **Phase 5 Complete**: Controllers are thin adapters delegating to use cases

## 📚 Next Steps

1. **Start with Phase 1.1**: Create domain exceptions
2. **Fix BaseEntity**: Resolve the created_at constructor bug
3. **Complete OrganizationEntity**: Add business logic and validation
4. **Work systematically**: Don't skip phases - each builds on the previous

This plan ensures you build from the foundation up, with each phase depending only on previously completed components.
