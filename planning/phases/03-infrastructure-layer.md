# Phase 3: Infrastructure Layer Implementation

## 🎯 What You'll Build

Implement concrete repository classes and dependency injection:

- ✅ Repository implementations for database access
- ✅ Dependency injection container setup
- ✅ Database transaction management
- ✅ Error handling and logging
- ✅ Integration with existing database models

## 📋 Prerequisites

- [x] [Application Layer Phase](../phases/02-application-layer.md) completed
- [x] Use cases and DTOs implemented
- [x] Domain entities and services working
- [x] Existing database models and DAOs available
- [x] 2-3 hours available

## 🛠️ Implementation Steps

### Step 1: Create Repository Implementations (25 minutes)

**Create file:** `infrastructure/database/repositories/sql_tenant_repository.py`

```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from domain.entities.tenant_entity import TenantEntity
from domain.repositories.tenant_repository import TenantRepository
from models.models import Tenant as TenantModel

class SQLTenantRepository(TenantRepository):
    """SQLAlchemy implementation of tenant repository"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, id: int) -> Optional[TenantEntity]:
        """Get tenant by ID"""
        stmt = select(TenantModel).where(TenantModel.id == id)
        result = await self._session.execute(stmt)
        tenant_model = result.scalar_one_or_none()
        
        return self._to_entity(tenant_model) if tenant_model else None
    
    async def get_by_organization(self, org_id: int) -> List[TenantEntity]:
        """Get all tenants for an organization"""
        stmt = select(TenantModel).where(TenantModel.organization_id == org_id)
        result = await self._session.execute(stmt)
        tenant_models = result.scalars().all()
        
        return [self._to_entity(model) for model in tenant_models]
    
    async def get_waitlist_tenants(self, org_id: int) -> List[TenantEntity]:
        """Get waitlist tenants for an organization"""
        stmt = select(TenantModel).where(
            (TenantModel.organization_id == org_id) & 
            (TenantModel.waitlist == True)
        )
        result = await self._session.execute(stmt)
        tenant_models = result.scalars().all()
        
        return [self._to_entity(model) for model in tenant_models]
    
    async def create(self, tenant: TenantEntity) -> TenantEntity:
        """Create a new tenant"""
        tenant_model = TenantModel(
            name=tenant.name,
            admission_date=tenant.admission_date,
            discharge_date=tenant.discharge_date,
            waitlist=tenant.is_waitlist,
            organization_id=tenant.organization_id
        )
        
        self._session.add(tenant_model)
        await self._session.commit()
        await self._session.refresh(tenant_model)
        
        return self._to_entity(tenant_model)
    
    async def update(self, tenant: TenantEntity) -> TenantEntity:
        """Update an existing tenant"""
        stmt = select(TenantModel).where(TenantModel.id == tenant.id)
        result = await self._session.execute(stmt)
        tenant_model = result.scalar_one_or_none()
        
        if not tenant_model:
            raise ValueError(f"Tenant with ID {tenant.id} not found")
        
        # Update fields
        tenant_model.name = tenant.name
        tenant_model.admission_date = tenant.admission_date
        tenant_model.discharge_date = tenant.discharge_date
        tenant_model.waitlist = tenant.is_waitlist
        
        await self._session.commit()
        await self._session.refresh(tenant_model)
        
        return self._to_entity(tenant_model)
    
    async def exists_by_name(self, name: str, org_id: int) -> bool:
        """Check if tenant exists by name in organization"""
        stmt = select(TenantModel).where(
            (TenantModel.name == name) & 
            (TenantModel.organization_id == org_id)
        )
        result = await self._session.execute(stmt)
        tenant_model = result.scalar_one_or_none()
        
        return tenant_model is not None
    
    def _to_entity(self, model: TenantModel) -> TenantEntity:
        """Convert database model to domain entity"""
        return TenantEntity(
            id=model.id,
            created_at=model.created_at,
            name=model.name,
            admission_date=model.admission_date,
            discharge_date=model.discharge_date,
            is_waitlist=model.waitlist,
            organization_id=model.organization_id
        )
```

### Step 2: Create User Repository Implementation (20 minutes)

**Create file:** `infrastructure/database/repositories/sql_user_repository.py`

```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from domain.entities.user_entity import UserEntity
from domain.repositories.user_repository import UserRepository
from models.models import User as UserModel

class SQLUserRepository(UserRepository):
    """SQLAlchemy implementation of user repository"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, id: int) -> Optional[UserEntity]:
        """Get user by ID"""
        stmt = select(UserModel).where(UserModel.id == id)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()
        
        return self._to_entity(user_model) if user_model else None
    
    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Get user by email"""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()
        
        return self._to_entity(user_model) if user_model else None
    
    async def get_by_organization(self, org_id: int) -> List[UserEntity]:
        """Get all users for an organization"""
        stmt = select(UserModel).where(UserModel.organization_id == org_id)
        result = await self._session.execute(stmt)
        user_models = result.scalars().all()
        
        return [self._to_entity(model) for model in user_models]
    
    async def create(self, user: UserEntity) -> UserEntity:
        """Create a new user"""
        user_model = UserModel(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            community_org=user.community_org,
            organization_id=user.organization_id
        )
        
        self._session.add(user_model)
        await self._session.commit()
        await self._session.refresh(user_model)
        
        return self._to_entity(user_model)
    
    async def update(self, user: UserEntity) -> UserEntity:
        """Update an existing user"""
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            raise ValueError(f"User with ID {user.id} not found")
        
        # Update fields
        user_model.email = user.email
        user_model.first_name = user.first_name
        user_model.last_name = user.last_name
        user_model.role = user.role
        user_model.community_org = user.community_org
        user_model.organization_id = user.organization_id
        
        await self._session.commit()
        await self._session.refresh(user_model)
        
        return self._to_entity(user_model)
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()
        
        return user_model is not None
    
    def _to_entity(self, model: UserModel) -> UserEntity:
        """Convert database model to domain entity"""
        return UserEntity(
            id=model.id,
            created_at=model.created_at,
            email=model.email,
            first_name=model.first_name,
            last_name=model.last_name,
            role=model.role,
            community_org=model.community_org,
            organization_id=model.organization_id
        )
```

### Step 3: Create Database Session Provider (15 minutes)

**Create file:** `infrastructure/database/session.py`

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://user:password@localhost/vacancy_portal"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging during development
    future=True,
)

# Create async session factory
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Step 4: Create Dependency Injection Container (20 minutes)

**Create file:** `infrastructure/container.py`

```python
from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

# Domain layer
from domain.repositories.tenant_repository import TenantRepository
from domain.repositories.user_repository import UserRepository
from domain.services.tenant_service import TenantService
from domain.services.user_service import UserService

# Application layer
from application.use_cases.tenant_use_cases import (
    CreateTenantUseCase, AdmitTenantUseCase, GetTenantUseCase, GetWaitlistTenantsUseCase
)
from application.use_cases.user_use_cases import (
    CreateUserUseCase, AuthenticateUserUseCase, UpdateUserRoleUseCase, GetUserUseCase
)
from application.services.tenant_management_service import TenantManagementService

# Infrastructure layer
from infrastructure.database.repositories.sql_tenant_repository import SQLTenantRepository
from infrastructure.database.repositories.sql_user_repository import SQLUserRepository
from infrastructure.database.session import get_db_session

class Container(containers.DeclarativeContainer):
    """Dependency injection container"""
    
    # Database session provider
    db_session = providers.Resource(get_db_session)
    
    # Repository implementations
    tenant_repository = providers.Factory(
        SQLTenantRepository,
        session=db_session
    )
    
    user_repository = providers.Factory(
        SQLUserRepository,
        session=db_session
    )
    
    # Domain services
    tenant_service = providers.Factory(
        TenantService,
        tenant_repository=tenant_repository
    )
    
    user_service = providers.Factory(
        UserService,
        user_repository=user_repository
    )
    
    # Use cases
    create_tenant_use_case = providers.Factory(
        CreateTenantUseCase,
        tenant_service=tenant_service
    )
    
    admit_tenant_use_case = providers.Factory(
        AdmitTenantUseCase,
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
    
    create_user_use_case = providers.Factory(
        CreateUserUseCase,
        user_service=user_service
    )
    
    authenticate_user_use_case = providers.Factory(
        AuthenticateUserUseCase,
        user_service=user_service
    )
    
    update_user_role_use_case = providers.Factory(
        UpdateUserRoleUseCase,
        user_service=user_service
    )
    
    get_user_use_case = providers.Factory(
        GetUserUseCase,
        user_service=user_service
    )
    
    # Application services
    tenant_management_service = providers.Factory(
        TenantManagementService,
        create_tenant_use_case=create_tenant_use_case,
        admit_tenant_use_case=admit_tenant_use_case,
        get_waitlist_use_case=get_waitlist_tenants_use_case
    )

# Global container instance
container = Container()
```

### Step 5: Create Dependency Injection Helpers (10 minutes)

**Create file:** `infrastructure/dependencies.py`

```python
from typing import AsyncGenerator
from dependency_injector.wiring import inject, Provide
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.container import container
from domain.repositories.tenant_repository import TenantRepository
from domain.repositories.user_repository import UserRepository
from domain.services.tenant_service import TenantService
from domain.services.user_service import UserService
from application.use_cases.tenant_use_cases import (
    CreateTenantUseCase, AdmitTenantUseCase, GetTenantUseCase, GetWaitlistTenantsUseCase
)
from application.use_cases.user_use_cases import (
    CreateUserUseCase, AuthenticateUserUseCase, UpdateUserRoleUseCase, GetUserUseCase
)
from application.services.tenant_management_service import TenantManagementService

# Repository dependencies
@inject
def get_tenant_repository(
    tenant_repo: TenantRepository = Provide[container.tenant_repository]
) -> TenantRepository:
    return tenant_repo

@inject
def get_user_repository(
    user_repo: UserRepository = Provide[container.user_repository]
) -> UserRepository:
    return user_repo

# Service dependencies
@inject
def get_tenant_service(
    tenant_service: TenantService = Provide[container.tenant_service]
) -> TenantService:
    return tenant_service

@inject
def get_user_service(
    user_service: UserService = Provide[container.user_service]
) -> UserService:
    return user_service

# Use case dependencies
@inject
def get_create_tenant_use_case(
    use_case: CreateTenantUseCase = Provide[container.create_tenant_use_case]
) -> CreateTenantUseCase:
    return use_case

@inject
def get_admit_tenant_use_case(
    use_case: AdmitTenantUseCase = Provide[container.admit_tenant_use_case]
) -> AdmitTenantUseCase:
    return use_case

@inject
def get_tenant_use_case(
    use_case: GetTenantUseCase = Provide[container.get_tenant_use_case]
) -> GetTenantUseCase:
    return use_case

@inject
def get_waitlist_tenants_use_case(
    use_case: GetWaitlistTenantsUseCase = Provide[container.get_waitlist_tenants_use_case]
) -> GetWaitlistTenantsUseCase:
    return use_case

@inject
def get_create_user_use_case(
    use_case: CreateUserUseCase = Provide[container.create_user_use_case]
) -> CreateUserUseCase:
    return use_case

@inject
def get_authenticate_user_use_case(
    use_case: AuthenticateUserUseCase = Provide[container.authenticate_user_use_case]
) -> AuthenticateUserUseCase:
    return use_case

@inject
def get_update_user_role_use_case(
    use_case: UpdateUserRoleUseCase = Provide[container.update_user_role_use_case]
) -> UpdateUserRoleUseCase:
    return use_case

@inject
def get_user_use_case(
    use_case: GetUserUseCase = Provide[container.get_user_use_case]
) -> GetUserUseCase:
    return use_case

# Application service dependencies
@inject
def get_tenant_management_service(
    service: TenantManagementService = Provide[container.tenant_management_service]
) -> TenantManagementService:
    return service
```

### Step 6: Create Database Initialization (15 minutes)

**Create file:** `infrastructure/database/init_db.py`

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

from models.models import Base
from infrastructure.database.session import engine

async def create_tables():
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_tables():
    """Drop all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def init_database():
    """Initialize database with tables"""
    print("Creating database tables...")
    await create_tables()
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_database())
```

## ✅ Success Criteria

- [ ] `infrastructure/database/repositories/` directory created
- [ ] `infrastructure/database/repositories/sql_tenant_repository.py` implemented
- [ ] `infrastructure/database/repositories/sql_user_repository.py` implemented
- [ ] `infrastructure/database/session.py` with async session management
- [ ] `infrastructure/container.py` with dependency injection setup
- [ ] `infrastructure/dependencies.py` with injection helpers
- [ ] `infrastructure/database/init_db.py` for database setup
- [ ] All dependencies properly wired
- [ ] Database transactions working correctly
- [ ] Error handling implemented

## 🧪 Testing Your Implementation

```bash
# Test infrastructure layer
pytest tests/infrastructure/ -v

# Test repository implementations
pytest tests/infrastructure/repositories/ -v

# Test dependency injection
pytest tests/infrastructure/container/ -v

# Integration tests with database
pytest tests/integration/ -v
```

## 🆘 Common Issues & Solutions

### Issue: SQLAlchemy Async Issues

RuntimeError: Task got bad yield

**Solution:** Ensure you're using SQLAlchemy 2.0+ with async support:

```bash
pip install sqlalchemy[asyncio]
```

### Issue: Dependency Injection Not Working

```python
ImportError: cannot import name 'Provide' from 'dependency_injector.wiring'
```

**Solution:** Install dependency-injector:

```bash
pip install dependency-injector
```

### Issue: Database Connection Errors

- Check your DATABASE_URL environment variable
- Ensure PostgreSQL is running
- Verify database credentials

### Issue: Repository Mapping Errors

- Ensure your domain entities match database model fields
- Check data type conversions between entities and models
- Verify primary key and foreign key relationships

## 📚 What You've Accomplished

### Before (Current Architecture)

```python
# Direct DAO usage in controllers
@tenant_router.post('/create-tenant')
def create_tenant(request: dict, db: Session = Depends(get_session)):
    return tenant_dao.create_tenant(request, db)
```

### After (Clean Architecture)

```python
# Dependency injection with abstractions
@tenant_router.post('/create-tenant')
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
):
    return await use_case.execute(request)

# Container wires everything together
container = Container()
container.tenant_repository.override(SQLTenantRepository(session))
```

## 🔄 Integration with Existing Code

### Option 1: Wire Up Existing Controllers (Recommended)

Update your existing controllers to use dependency injection:

```python
# In your main.py or controller files
from infrastructure.dependencies import get_create_tenant_use_case
from infrastructure.container import container

# Wire the container
container.wire(modules=[__name__])

# Update existing controller
@tenant_router.post('/create-tenant')
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
):
    return await use_case.execute(request)
```

### Option 2: Gradual Migration

Keep existing controllers working while adding new clean architecture endpoints:

```python
# New clean endpoints
@tenant_router.post('/v2/tenants')
async def create_tenant_v2(request: CreateTenantRequest):
    # Uses clean architecture

# Legacy endpoints (keep working)
@tenant_router.post('/tenants')
def create_tenant_v1(request: dict, db: Session):
    # Uses existing DAO logic
```

## 📈 Benefits Achieved

### Developer Experience

- ✅ **Zero coupling** - Domain layer independent of database technology
- ✅ **Easy testing** - Mock repositories for unit tests
- ✅ **Framework flexibility** - Swap databases without touching business logic
- ✅ **Clear dependencies** - Explicit dependency injection

### Code Quality

- ✅ **Dependency inversion** - High-level modules don't depend on low-level modules
- ✅ **Single responsibility** - Each repository handles one entity type
- ✅ **Consistent patterns** - All repositories follow same interface
- ✅ **Transaction management** - Proper database session handling

### Business Value

- ✅ **Database portability** - Easy to migrate to different databases
- ✅ **Scalability** - Clear separation enables horizontal scaling
- ✅ **Maintainability** - Changes localized to infrastructure layer
- ✅ **Future-proof** - Can adopt new technologies without affecting business logic

## 🎯 Next Steps

Once your infrastructure layer is complete:

1. **Presentation Layer**: Create controllers using clean architecture (optional)
2. **Testing**: Add comprehensive integration tests
3. **Migration**: Gradually replace existing DAO usage
4. **Monitoring**: Add logging and error tracking

## 📖 Additional Resources

- [Repository Pattern Explained](../patterns/repositories.md)
- [Dependency Injection Guide](../patterns/dependency-injection.md)
- [Database Integration Patterns](../patterns/database-integration.md)
- [Presentation Layer Guide](../phases/04-presentation-layer.md)

## 🏆 Phase 3 Complete

You've successfully implemented a complete infrastructure layer with:

- ✅ **Repository implementations** for database access
- ✅ **Dependency injection container** for managing dependencies
- ✅ **Async database sessions** with proper transaction management
- ✅ **Error handling** and data mapping between layers
- ✅ **Integration** with existing database models
- ✅ **Testing support** through dependency injection

**🎉 Congratulations!** Your infrastructure layer now provides concrete implementations while keeping the domain layer completely independent.

---

**Ready for Phase 4?** → [Presentation Layer Guide](04-presentation-layer.md)
