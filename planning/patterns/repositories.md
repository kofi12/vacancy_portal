# 📚 Repository Pattern

## Overview

Repositories provide a uniform interface for accessing domain entities, abstracting the underlying data storage mechanism.

## Key Characteristics

### ✅ What Repositories Should Provide

- **Uniform Interface** - Same methods regardless of storage technology
- **Domain Entity Focus** - Work with domain entities, not database models
- **Query Abstraction** - Hide complex query logic
- **Transaction Management** - Handle database transactions

### ❌ What Repositories Should NOT Do

- Business logic (belongs in domain services)
- Data transformation (belongs in infrastructure layer)
- HTTP concerns
- Caching logic (separate concern)

## Interface Pattern

### Repository Interface

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

## Implementation Patterns

### SQLAlchemy Implementation

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from infrastructure.database.repositories.base_repository import BaseRepository

class SQLTenantRepository(TenantRepository, BaseRepository):
    """SQLAlchemy implementation of tenant repository"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, id: int) -> Optional[TenantEntity]:
        """Get tenant by ID"""
        stmt = select(TenantModel).where(TenantModel.id == id)
        result = await self._session.execute(stmt)
        tenant_model = result.scalar_one_or_none()
        
        return self._to_entity(tenant_model) if tenant_model else None
    
    async def create(self, tenant: TenantEntity) -> TenantEntity:
        """Create a new tenant"""
        tenant_model = TenantModel(
            name=tenant.name,
            admission_date=tenant.admission_date,
            waitlist=tenant.is_waitlist,
            organization_id=tenant.organization_id
        )
        
        self._session.add(tenant_model)
        await self._session.commit()
        await self._session.refresh(tenant_model)
        
        return self._to_entity(tenant_model)
    
    def _to_entity(self, model) -> TenantEntity:
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

### Base Repository Pattern

```python
from abc import ABC
from typing import TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession

TEntity = TypeVar('TEntity')
TModel = TypeVar('TModel')

class BaseRepository(ABC, Generic[TEntity, TModel]):
    """Base repository with common functionality"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def _commit(self):
        """Commit transaction"""
        await self._session.commit()
    
    async def _refresh(self, model):
        """Refresh model after commit"""
        await self._session.refresh(model)
    
    def _add_to_session(self, model):
        """Add model to session"""
        self._session.add(model)
```

## Query Patterns

### Simple Query Pattern

```python
async def get_by_organization(self, org_id: int) -> List[TenantEntity]:
    """Get all tenants for an organization"""
    stmt = select(TenantModel).where(TenantModel.organization_id == org_id)
    result = await self._session.execute(stmt)
    tenant_models = result.scalars().all()
    
    return [self._to_entity(model) for model in tenant_models]
```

### Complex Query Pattern

```python
async def get_waitlist_tenants(self, org_id: int) -> List[TenantEntity]:
    """Get waitlist tenants for an organization"""
    stmt = select(TenantModel).where(
        and_(
            TenantModel.organization_id == org_id,
            TenantModel.waitlist == True,
            TenantModel.admission_date.is_(None)
        )
    ).order_by(TenantModel.created_at)
    
    result = await self._session.execute(stmt)
    tenant_models = result.scalars().all()
    
    return [self._to_entity(model) for model in tenant_models]
```

### Existence Check Pattern

```python
async def exists_by_name(self, name: str, org_id: int) -> bool:
    """Check if tenant exists by name in organization"""
    stmt = select(exists(
        select(TenantModel.id).where(
            and_(
                TenantModel.name == name,
                TenantModel.organization_id == org_id
            )
        )
    ))
    
    result = await self._session.execute(stmt)
    return result.scalar()
```

## Error Handling Patterns

### Repository Exception Pattern

```python
class RepositoryException(Exception):
    """Base repository exception"""
    pass

class EntityNotFoundError(RepositoryException):
    """Raised when entity is not found"""
    pass

class ConcurrencyError(RepositoryException):
    """Raised on concurrent update conflicts"""
    pass

# Usage in repository
async def update(self, tenant: TenantEntity) -> TenantEntity:
    """Update tenant with error handling"""
    try:
        # Update logic here
        return updated_tenant
    except IntegrityError:
        raise ConcurrencyError("Tenant was modified by another process")
    except Exception as e:
        raise RepositoryException(f"Failed to update tenant: {str(e)}")
```

## Testing Patterns

### Repository Unit Test Pattern

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def repository(mock_session):
    return SQLTenantRepository(mock_session)

@pytest.mark.asyncio
async def test_get_by_id_success(repository, mock_session):
    # Arrange
    tenant_model = MagicMock()
    tenant_model.id = 1
    tenant_model.name = "Test Tenant"
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = tenant_model
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_id(1)
    
    # Assert
    assert result.id == 1
    assert result.name == "Test Tenant"
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_by_id_not_found(repository, mock_session):
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_id(999)
    
    # Assert
    assert result is None
```

### Repository Integration Test Pattern

```python
@pytest.mark.asyncio
async def test_create_tenant_integration(db_session):
    """Integration test with real database"""
    # Arrange
    repository = SQLTenantRepository(db_session)
    tenant = TenantEntity.create_tenant("Integration Test", 1)
    
    # Act
    created = await repository.create(tenant)
    
    # Assert
    assert created.id is not None
    assert created.name == "Integration Test"
    
    # Verify in database
    retrieved = await repository.get_by_id(created.id)
    assert retrieved.name == "Integration Test"
```

## Performance Patterns

### Connection Pooling Pattern

```python
# In session configuration
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,          # Connection pool size
    max_overflow=20,       # Max overflow connections
    pool_recycle=3600,    # Recycle connections after 1 hour
    pool_pre_ping=True,   # Test connections before use
)
```

### Query Optimization Pattern

```python
async def get_tenants_with_organization(self, org_id: int):
    """Optimized query with join"""
    stmt = select(TenantModel, OrganizationModel).join(
        OrganizationModel,
        TenantModel.organization_id == OrganizationModel.id
    ).where(TenantModel.organization_id == org_id)
    
    result = await self._session.execute(stmt)
    return result.all()
```

## Best Practices

### 1. **Keep Repository Interfaces Small**

```python
# ✅ Good: Focused interface
class TenantRepository(ABC):
    async def get_by_id(self, id: int): pass
    async def create(self, tenant): pass

# ❌ Bad: Too many methods
class TenantRepository(ABC):
    async def get_by_id(self, id: int): pass
    async def get_by_name(self, name: str): pass
    async def get_by_org_and_name(self, org_id, name): pass
    async def get_active_by_org(self, org_id): pass
    # ... many more methods
```

### 2. **Use Specifications for Complex Queries**

```python
# Specification pattern for complex queries
class TenantSpecification:
    def __init__(self, org_id: Optional[int] = None, is_waitlist: Optional[bool] = None):
        self.org_id = org_id
        self.is_waitlist = is_waitlist
    
    def to_query(self):
        conditions = []
        if self.org_id:
            conditions.append(TenantModel.organization_id == self.org_id)
        if self.is_waitlist is not None:
            conditions.append(TenantModel.waitlist == self.is_waitlist)
        return and_(*conditions) if conditions else True

# Usage
async def find_by_specification(self, spec: TenantSpecification):
    stmt = select(TenantModel).where(spec.to_query())
    # Execute query
```

### 3. **Handle Transactions Properly**

```python
async def create_with_related_data(self, tenant: TenantEntity, org_data):
    """Transaction with multiple operations"""
    async with self._session.begin():
        try:
            # Create tenant
            created_tenant = await self.create(tenant)
            
            # Update organization stats
            await self._update_org_stats(created_tenant.organization_id)
            
            return created_tenant
        except Exception:
            # Transaction will rollback automatically
            raise
```

### 4. **Implement Pagination**

```python
from sqlalchemy import func

async def get_paginated(self, page: int = 1, size: int = 20, org_id: Optional[int] = None):
    """Paginated query with total count"""
    query = select(TenantModel)
    if org_id:
        query = query.where(TenantModel.organization_id == org_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await self._session.execute(count_query)
    total_count = total.scalar()
    
    # Get paginated results
    paginated_query = query.offset((page - 1) * size).limit(size)
    result = await self._session.execute(paginated_query)
    items = result.scalars().all()
    
    return {
        'items': [self._to_entity(item) for item in items],
        'total': total_count,
        'page': page,
        'size': size,
        'pages': (total_count + size - 1) // size
    }
```

This pattern ensures your repositories provide a clean, uniform interface to domain entities while abstracting the underlying storage complexity.
