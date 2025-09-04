# 🔄 Migrating from DAO to Repository Pattern

## Overview

This guide shows how to migrate from Data Access Objects (DAOs) to Clean Architecture Repository pattern.

## Current DAO vs Repository Pattern

### ❌ Current DAO Pattern

```python
# database/tenant_dao.py
def create_tenant(tenant_data, db: Session):
    """DAO with mixed concerns"""
    # ❌ Business logic in DAO
    if not tenant_exists(tenant_data, db):
        tenant = Tenant(**tenant_data)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

def get_tenant(id: int, db: Session):
    """DAO with raw SQLAlchemy"""
    # ❌ Direct database model exposure
    statement = select(Tenant).where(id == Tenant.id)
    result = db.exec(statement).first()
    return result

def tenant_exists(tenant_data, db: Session) -> bool:
    """DAO with business logic"""
    # ❌ Business rule in data access layer
    name = tenant_data.name
    tenant = get_tenant_by_name(name, db)
    if tenant is None:
        return False
    return True
```

### ✅ Repository Pattern

```python
# domain/repositories/tenant_repository.py
class TenantRepository(ABC):
    """Repository interface - no implementation"""
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[TenantEntity]:
        pass
    
    @abstractmethod
    async def create(self, tenant: TenantEntity) -> TenantEntity:
        pass
    
    @abstractmethod
    async def exists_by_name(self, name: str, org_id: int) -> bool:
        pass

# infrastructure/database/repositories/sql_tenant_repository.py
class SQLTenantRepository(TenantRepository):
    """Repository implementation"""
    
    async def get_by_id(self, id: int) -> Optional[TenantEntity]:
        stmt = select(TenantModel).where(TenantModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def create(self, tenant: TenantEntity) -> TenantEntity:
        # Convert domain entity to database model
        tenant_model = TenantModel(
            name=tenant.name,
            organization_id=tenant.organization_id
        )
        self._session.add(tenant_model)
        await self._session.commit()
        return self._to_entity(tenant_model)
    
    def _to_entity(self, model) -> TenantEntity:
        """Convert database model to domain entity"""
        return TenantEntity(
            id=model.id,
            created_at=model.created_at,
            name=model.name,
            organization_id=model.organization_id
        )
```

## Step-by-Step Migration

### Step 1: Create Repository Interface

**Create file:** `domain/repositories/tenant_repository.py`

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.tenant_entity import TenantEntity

class TenantRepository(ABC):
    """Repository interface for tenant data access"""
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[TenantEntity]:
        """Get tenant by ID"""
        pass
    
    @abstractmethod
    async def get_by_organization(self, org_id: int) -> List[TenantEntity]:
        """Get all tenants for an organization"""
        pass
    
    @abstractmethod
    async def create(self, tenant: TenantEntity) -> TenantEntity:
        """Create a new tenant"""
        pass
    
    @abstractmethod
    async def update(self, tenant: TenantEntity) -> TenantEntity:
        """Update an existing tenant"""
        pass
    
    @abstractmethod
    async def exists_by_name(self, name: str, org_id: int) -> bool:
        """Check if tenant exists by name in organization"""
        pass
```

### Step 2: Create Repository Implementation

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
        stmt = select(TenantModel).where(TenantModel.id == id)
        result = await self._session.execute(stmt)
        tenant_model = result.scalar_one_or_none()
        
        return self._to_entity(tenant_model) if tenant_model else None
    
    async def get_by_organization(self, org_id: int) -> List[TenantEntity]:
        stmt = select(TenantModel).where(TenantModel.organization_id == org_id)
        result = await self._session.execute(stmt)
        tenant_models = result.scalars().all()
        
        return [self._to_entity(model) for model in tenant_models]
    
    async def create(self, tenant: TenantEntity) -> TenantEntity:
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

### Step 3: Move Business Logic Out of DAO

**Identify and extract business logic:**

```python
# ❌ Business logic currently in DAO
def create_tenant(tenant_data, db: Session):
    if not tenant_exists(tenant_data, db):  # Business rule
        # Creation logic
        pass

# ✅ Move business logic to domain service
class TenantService:
    async def create_tenant(self, tenant: TenantEntity) -> TenantEntity:
        # Business rule moved here
        if await self._repository.exists_by_name(tenant.name, tenant.organization_id):
            raise TenantAlreadyExistsError()
        
        return await self._repository.create(tenant)
```

### Step 4: Update Controllers to Use Repositories

**Before:**

```python
# ❌ Direct DAO usage
@tenant_router.post('/create-tenant')
def create_tenant(request: dict, db: Session = Depends(get_session)):
    return tenant_dao.create_tenant(request, db)
```

**After:**

```python
# ✅ Repository through dependency injection
@tenant_router.post('/create-tenant')
async def create_tenant(
    request: CreateTenantRequest,
    repository: TenantRepository = Depends(get_tenant_repository)
):
    tenant = TenantEntity.create_tenant(request.name, request.organization_id)
    return await repository.create(tenant)
```

### Step 5: Update Dependency Injection

**Update container.py:**

```python
class Container(containers.DeclarativeContainer):
    db_session = providers.Resource(get_db_session)
    
    tenant_repository = providers.Factory(
        SQLTenantRepository,
        session=db_session
    )
    
    # Add repository dependency
    get_tenant_repository = providers.Factory(
        lambda repo: repo,
        repo=tenant_repository
    )
```

## Advanced Migration Patterns

### Complex Query Migration

**Before (DAO):**

```python
def get_complex_tenant_data(org_id: int, db: Session):
    """Complex query with joins and filtering"""
    return db.query(Tenant, Organization).join(
        Organization, Tenant.organization_id == Organization.id
    ).filter(
        Tenant.organization_id == org_id,
        Tenant.waitlist == True
    ).all()
```

**After (Repository):**

```python
async def get_complex_tenant_data(self, org_id: int) -> List[TenantWithOrg]:
    """Complex query with proper typing"""
    stmt = select(TenantModel, OrganizationModel).join(
        OrganizationModel,
        TenantModel.organization_id == OrganizationModel.id
    ).where(
        and_(
            TenantModel.organization_id == org_id,
            TenantModel.waitlist == True
        )
    )
    
    result = await self._session.execute(stmt)
    return result.all()

@dataclass
class TenantWithOrg:
    """DTO for complex query result"""
    tenant: TenantEntity
    organization_name: str
```

### Transaction Management Migration

**Before (DAO):**

```python
def create_tenant_with_org_update(tenant_data, org_update_data, db: Session):
    """Manual transaction management"""
    try:
        tenant = create_tenant(tenant_data, db)
        update_organization(org_update_data, db)
        db.commit()
        return tenant
    except:
        db.rollback()
        raise
```

**After (Repository):**

```python
async def create_tenant_with_org_update(self, tenant: TenantEntity, org_update):
    """Automatic transaction management"""
    async with self._session.begin():
        created_tenant = await self.create(tenant)
        await self._update_organization(org_update)
        return created_tenant
```

## Testing Migration

### Before: Hard to Test DAOs

```python
def test_create_tenant():
    # Requires real database
    db = get_test_db()
    result = tenant_dao.create_tenant({"name": "Test"}, db)
    assert result.name == "Test"
```

### After: Easy to Test Repositories

```python
def test_create_tenant():
    # Mock the session
    mock_session = AsyncMock()
    repository = SQLTenantRepository(mock_session)
    
    tenant = TenantEntity.create_tenant("Test", 1)
    result = await repository.create(tenant)
    
    # Verify session methods called correctly
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    assert result.name == "Test"
```

## Error Handling Migration

### Before: Database Exceptions in DAO

```python
def create_tenant(tenant_data, db: Session):
    try:
        tenant = Tenant(**tenant_data)
        db.add(tenant)
        db.commit()
        return tenant
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Duplicate tenant")
```

### After: Domain Exceptions in Repository

```python
class RepositoryException(Exception):
    """Base repository exception"""
    pass

async def create(self, tenant: TenantEntity) -> TenantEntity:
    try:
        # Creation logic
        return created_tenant
    except IntegrityError as e:
        raise RepositoryException(f"Failed to create tenant: {str(e)}")
    except Exception as e:
        await self._session.rollback()
        raise RepositoryException(f"Unexpected error: {str(e)}")
```

## Performance Considerations

### Query Optimization

**Before (DAO):**

```python
def get_tenants_with_lazy_loading(org_id: int, db: Session):
    """N+1 query problem"""
    tenants = db.query(Tenant).filter(Tenant.organization_id == org_id).all()
    for tenant in tenants:
        org = tenant.organization  # Lazy load - N+1 queries
    return tenants
```

**After (Repository):**

```python
async def get_tenants_with_organizations(self, org_id: int):
    """Single optimized query"""
    stmt = select(TenantModel, OrganizationModel).join(
        OrganizationModel,
        TenantModel.organization_id == OrganizationModel.id
    ).where(TenantModel.organization_id == org_id)
    
    result = await self._session.execute(stmt)
    return result.all()  # Single query with join
```

### Connection Pooling

**Repository-level connection management:**

```python
class SQLTenantRepository(TenantRepository):
    def __init__(self, session_factory):
        self._session_factory = session_factory
    
    async def _get_session(self):
        """Get session from pool"""
        return self._session_factory()
    
    async def get_by_id(self, id: int) -> Optional[TenantEntity]:
        async with self._get_session() as session:
            stmt = select(TenantModel).where(TenantModel.id == id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None
```

## Migration Checklist

### Phase 1: Interface Creation

- [ ] Create repository interfaces
- [ ] Define method signatures
- [ ] Add proper type hints
- [ ] Document method purposes

### Phase 2: Implementation

- [ ] Create repository implementations
- [ ] Implement data mapping methods
- [ ] Add error handling
- [ ] Implement transaction management

### Phase 3: Business Logic Extraction

- [ ] Move business rules from DAOs to domain services
- [ ] Update controllers to use repositories
- [ ] Remove business logic from data access layer
- [ ] Update error handling

### Phase 4: Testing

- [ ] Create unit tests for repositories
- [ ] Create integration tests
- [ ] Test error scenarios
- [ ] Verify performance

### Phase 5: Optimization

- [ ] Optimize queries
- [ ] Add connection pooling
- [ ] Implement caching if needed
- [ ] Add monitoring

## Common Migration Challenges

### 1. **Complex Existing DAOs**

**Problem:** DAOs with 200+ lines mixing concerns
**Solution:** Break into multiple focused repositories

### 2. **Tight Coupling**

**Problem:** DAOs used directly in many places
**Solution:** Use dependency injection with interfaces

### 3. **Performance Regressions**

**Problem:** Repository pattern introduces overhead
**Solution:** Optimize queries and use connection pooling

### 4. **Transaction Management**

**Problem:** Complex transaction logic in DAOs
**Solution:** Move to repository level with proper session management

## Rollback Strategy

### Quick Rollback

```python
# Feature flag for repository usage
USE_REPOSITORIES = os.getenv('USE_REPOSITORIES', 'false').lower() == 'true'

if USE_REPOSITORIES:
    # Use new repository
    tenant = await tenant_repository.create(tenant_entity)
else:
    # Use old DAO
    tenant = tenant_dao.create_tenant(tenant_data, db)
```

### Gradual Rollback

1. Switch feature flag to disable repositories
2. Controllers automatically use DAOs again
3. Repository code remains for future use
4. No service disruption

## Success Metrics

### Code Quality

- ✅ **Separation of concerns**: No business logic in repositories
- ✅ **Testability**: 80%+ test coverage for repositories
- ✅ **Maintainability**: Clear data access patterns
- ✅ **Type safety**: Strong typing throughout

### Performance

- ✅ **Query efficiency**: Optimized database access
- ✅ **Connection pooling**: Proper resource management
- ✅ **Response time**: No degradation
- ✅ **Scalability**: Handle increased load

## Next Steps

After repository migration:

1. **Remove legacy DAOs** (once repositories are proven)
2. **Update domain services** to use repositories
3. **Implement application services** for complex workflows
4. **Add comprehensive integration tests**

This migration transforms your data access layer from tightly-coupled DAOs to clean, testable repositories that follow Clean Architecture principles.
