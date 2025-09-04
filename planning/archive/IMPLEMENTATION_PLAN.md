# Implementation Plan: Refactoring to Clean Architecture

## Phase 1: Domain Layer Implementation

### 1.1 Domain Entities

```python
# domain/entities/base_entity.py
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

class BaseEntity(ABC):
    def __init__(self, id: Optional[int] = None, created_at: Optional[datetime] = None):
        self._id = id
        self._created_at = created_at or datetime.utcnow()
    
    @property
    def id(self) -> Optional[int]:
        return self._id
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
```

```python
# domain/entities/tenant.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .base_entity import BaseEntity

@dataclass
class Tenant(BaseEntity):
    name: str
    admission_date: Optional[datetime] = None
    discharge_date: Optional[datetime] = None
    waitlist: bool = False
    organization_id: int = None
    
    def is_active(self) -> bool:
        return self.discharge_date is None
    
    def is_on_waitlist(self) -> bool:
        return self.waitlist
```

### 1.2 Repository Interfaces (Dependency Inversion)

```python
# domain/repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from domain.entities.base_entity import BaseEntity

T = TypeVar('T', bound=BaseEntity)

class BaseRepository(Generic[T], ABC):
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass
    
    @abstractmethod
    async def list_all(self) -> List[T]:
        pass
```

```python
# domain/repositories/tenant_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.tenant import Tenant
from .base_repository import BaseRepository

class TenantRepository(BaseRepository[Tenant], ABC):
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Tenant]:
        pass
    
    @abstractmethod
    async def get_waitlist_tenants(self) -> List[Tenant]:
        pass
    
    @abstractmethod
    async def get_active_tenants(self) -> List[Tenant]:
        pass
    
    @abstractmethod
    async def get_by_organization(self, organization_id: int) -> List[Tenant]:
        pass
```

### 1.3 Domain Services

```python
# domain/services/tenant_service.py
from typing import List, Optional
from domain.entities.tenant import Tenant
from domain.repositories.tenant_repository import TenantRepository
from domain.exceptions import TenantNotFoundError, TenantAlreadyExistsError

class TenantService:
    def __init__(self, tenant_repository: TenantRepository):
        self._tenant_repository = tenant_repository
    
    async def create_tenant(self, tenant: Tenant) -> Tenant:
        # Business logic: check if tenant already exists
        existing_tenant = await self._tenant_repository.get_by_name(tenant.name)
        if existing_tenant:
            raise TenantAlreadyExistsError(f"Tenant with name {tenant.name} already exists")
        
        return await self._tenant_repository.create(tenant)
    
    async def get_tenant(self, tenant_id: int) -> Tenant:
        tenant = await self._tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant with id {tenant_id} not found")
        return tenant
    
    async def get_waitlist_tenants(self) -> List[Tenant]:
        return await self._tenant_repository.get_waitlist_tenants()
    
    async def get_active_tenants(self) -> List[Tenant]:
        return await self._tenant_repository.get_active_tenants()
```

### 1.4 Domain Exceptions

```python
# domain/exceptions/__init__.py
class DomainException(Exception):
    """Base exception for domain layer"""
    pass

class TenantNotFoundError(DomainException):
    pass

class TenantAlreadyExistsError(DomainException):
    pass

class UserNotFoundError(DomainException):
    pass

class UserAlreadyExistsError(DomainException):
    pass

class OrganizationNotFoundError(DomainException):
    pass

class OrganizationAlreadyExistsError(DomainException):
    pass
```

## Phase 2: Application Layer Implementation

### 2.1 Use Cases

```python
# application/use_cases/tenant_use_cases.py
from typing import List
from domain.entities.tenant import Tenant
from domain.services.tenant_service import TenantService
from application.dto.tenant_dto import CreateTenantRequest, UpdateTenantRequest, TenantResponse

class CreateTenantUseCase:
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self, request: CreateTenantRequest) -> TenantResponse:
        tenant = Tenant(
            name=request.name,
            admission_date=request.admission_date,
            organization_id=request.organization_id,
            waitlist=request.waitlist
        )
        
        created_tenant = await self._tenant_service.create_tenant(tenant)
        return TenantResponse.from_entity(created_tenant)

class GetTenantUseCase:
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self, tenant_id: int) -> TenantResponse:
        tenant = await self._tenant_service.get_tenant(tenant_id)
        return TenantResponse.from_entity(tenant)

class GetWaitlistTenantsUseCase:
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self) -> List[TenantResponse]:
        tenants = await self._tenant_service.get_waitlist_tenants()
        return [TenantResponse.from_entity(tenant) for tenant in tenants]
```

### 2.2 DTOs (Data Transfer Objects)

```python
# application/dto/tenant_dto.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from domain.entities.tenant import Tenant

@dataclass
class CreateTenantRequest:
    name: str
    admission_date: Optional[datetime] = None
    organization_id: int = None
    waitlist: bool = False

@dataclass
class UpdateTenantRequest:
    name: Optional[str] = None
    admission_date: Optional[datetime] = None
    discharge_date: Optional[datetime] = None
    waitlist: Optional[bool] = None
    organization_id: Optional[int] = None

@dataclass
class TenantResponse:
    id: int
    name: str
    admission_date: Optional[datetime]
    discharge_date: Optional[datetime]
    waitlist: bool
    organization_id: int
    created_at: datetime
    
    @classmethod
    def from_entity(cls, tenant: Tenant) -> 'TenantResponse':
        return cls(
            id=tenant.id,
            name=tenant.name,
            admission_date=tenant.admission_date,
            discharge_date=tenant.discharge_date,
            waitlist=tenant.waitlist,
            organization_id=tenant.organization_id,
            created_at=tenant.created_at
        )
```

## Phase 3: Infrastructure Layer Implementation

### 3.1 Repository Implementations

```python
# infrastructure/database/repositories/sql_tenant_repository.py
from typing import List, Optional
from sqlmodel import Session, select
from domain.entities.tenant import Tenant
from domain.repositories.tenant_repository import TenantRepository
from infrastructure.database.models.tenant_model import TenantModel

class SQLTenantRepository(TenantRepository):
    def __init__(self, session: Session):
        self._session = session
    
    async def create(self, tenant: Tenant) -> Tenant:
        tenant_model = TenantModel(
            name=tenant.name,
            admission_date=tenant.admission_date,
            discharge_date=tenant.discharge_date,
            waitlist=tenant.waitlist,
            organization_id=tenant.organization_id
        )
        
        self._session.add(tenant_model)
        self._session.commit()
        self._session.refresh(tenant_model)
        
        return self._to_entity(tenant_model)
    
    async def get_by_id(self, id: int) -> Optional[Tenant]:
        statement = select(TenantModel).where(TenantModel.id == id)
        result = self._session.exec(statement).first()
        return self._to_entity(result) if result else None
    
    async def get_by_name(self, name: str) -> Optional[Tenant]:
        statement = select(TenantModel).where(TenantModel.name == name)
        result = self._session.exec(statement).first()
        return self._to_entity(result) if result else None
    
    async def get_waitlist_tenants(self) -> List[Tenant]:
        statement = select(TenantModel).where(TenantModel.waitlist == True)
        results = self._session.exec(statement).all()
        return [self._to_entity(result) for result in results]
    
    async def get_active_tenants(self) -> List[Tenant]:
        statement = select(TenantModel).where(TenantModel.discharge_date.is_(None))
        results = self._session.exec(statement).all()
        return [self._to_entity(result) for result in results]
    
    def _to_entity(self, model: TenantModel) -> Tenant:
        return Tenant(
            id=model.id,
            name=model.name,
            admission_date=model.admission_date,
            discharge_date=model.discharge_date,
            waitlist=model.waitlist,
            organization_id=model.organization_id,
            created_at=model.created_at
        )
```

### 3.2 Dependency Injection Container

```python
# infrastructure/container.py
from dependency_injector import containers, providers
from infrastructure.database.repositories.sql_tenant_repository import SQLTenantRepository
from infrastructure.database.repositories.sql_user_repository import SQLUserRepository
from infrastructure.database.repositories.sql_organization_repository import SQLOrganizationRepository
from domain.services.tenant_service import TenantService
from domain.services.user_service import UserService
from domain.services.organization_service import OrganizationService
from application.use_cases.tenant_use_cases import CreateTenantUseCase, GetTenantUseCase, GetWaitlistTenantsUseCase

class Container(containers.DeclarativeContainer):
    # Database session
    session = providers.Singleton(lambda: Session(engine))
    
    # Repositories
    tenant_repository = providers.Factory(
        SQLTenantRepository,
        session=session
    )
    
    user_repository = providers.Factory(
        SQLUserRepository,
        session=session
    )
    
    organization_repository = providers.Factory(
        SQLOrganizationRepository,
        session=session
    )
    
    # Domain Services
    tenant_service = providers.Factory(
        TenantService,
        tenant_repository=tenant_repository
    )
    
    user_service = providers.Factory(
        UserService,
        user_repository=user_repository
    )
    
    organization_service = providers.Factory(
        OrganizationService,
        organization_repository=organization_repository
    )
    
    # Use Cases
    create_tenant_use_case = providers.Factory(
        CreateTenantUseCase,
        tenant_service=tenant_service
    )
    
    get_tenant_use_case = providers.Factory(
        GetTenantUseCase,
        tenant_service=tenant_service
    )
    
    get_waitlist_tenants_use_case = providers.Factory(
        GetWaitlistTenantsUseCase,
        tenant_service=tenant_service
    )
```

## Phase 4: Presentation Layer Implementation

### 4.1 Refactored Controllers

```python
# presentation/controllers/tenant_controller.py
from fastapi import APIRouter, Depends, HTTPException, Security
from typing import List
from application.dto.tenant_dto import CreateTenantRequest, UpdateTenantRequest, TenantResponse
from application.use_cases.tenant_use_cases import CreateTenantUseCase, GetTenantUseCase, GetWaitlistTenantsUseCase
from presentation.dependencies import get_current_user_with_scopes
from presentation.serializers.tenant_serializer import TenantSerializer

tenant_router = APIRouter(prefix='/api/tenants')

@tenant_router.post('/create-tenant', response_model=TenantResponse, tags=["Tenants"])
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(),
    current_user = Security(get_current_user_with_scopes, scopes=["write:tenants"])
):
    try:
        return await use_case.execute(request)
    except TenantAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

@tenant_router.get('/tenant/{tenant_id}', response_model=TenantResponse, tags=["Tenants"])
async def get_tenant(
    tenant_id: int,
    use_case: GetTenantUseCase = Depends(),
    current_user = Security(get_current_user_with_scopes, scopes=["view:tenants"])
):
    try:
        return await use_case.execute(tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@tenant_router.get('/waitlist', response_model=List[TenantResponse], tags=["Tenants"])
async def get_waitlist(
    use_case: GetWaitlistTenantsUseCase = Depends(),
    current_user = Security(get_current_user_with_scopes, scopes=["view:waitlist"])
):
    return await use_case.execute()
```

### 4.2 Dependencies

```python
# presentation/dependencies.py
from fastapi import Depends
from infrastructure.container import Container

def get_container() -> Container:
    return Container()

def get_current_user_with_scopes(
    container: Container = Depends(get_container),
    # ... other dependencies
):
    # Implementation
    pass
```

## Migration Strategy

### Step 1: Create New Structure

1. Create new directory structure
2. Implement domain entities and interfaces
3. Create basic repository implementations

### Step 2: Gradual Migration

1. Migrate one entity at a time (start with Tenant)
2. Create new controllers alongside old ones
3. Test thoroughly before removing old code

### Step 3: Update Dependencies

1. Update main.py to use new container
2. Migrate authentication to new structure
3. Update all imports and dependencies

### Step 4: Clean Up

1. Remove old code
2. Update tests
3. Update documentation

## Benefits Achieved

1. **Low Coupling**: Controllers depend on interfaces, not concrete implementations
2. **High Cohesion**: Each class has a single, well-defined responsibility
3. **Testability**: Easy to mock dependencies and test in isolation
4. **Extensibility**: New features can be added without modifying existing code
5. **Maintainability**: Clear separation of concerns makes code easier to understand and modify
