# 🗄️ Database Integration Pattern

## Overview

Database integration patterns ensure clean separation between business logic and data persistence while maintaining performance and reliability.

## Connection Management

### Async Connection Pool Pattern

```python
# infrastructure/database/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/vacancy_portal")

# Create async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    # Connection pool settings
    pool_size=10,              # Base pool size
    max_overflow=20,           # Max additional connections
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Test connections before use
    pool_reset_on_return=True, # Reset connection state
    
    # Performance settings
    echo=False,                # Disable SQL logging in production
    future=True,               # Use SQLAlchemy 2.0 style
)

# Create async session factory
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,    # Keep objects usable after commit
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions"""
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

### Transaction Management Pattern

```python
# infrastructure/database/transaction.py
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator, Callable, Any
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def transaction_context(session: AsyncSession):
    """Context manager for database transactions"""
    try:
        async with session.begin():
            yield session
        logger.debug("Transaction committed successfully")
    except Exception as e:
        logger.error(f"Transaction rolled back due to: {str(e)}")
        raise

class TransactionManager:
    """Manages database transactions across multiple operations"""
    
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory
    
    @asynccontextmanager
    async def transaction(self):
        """Transaction context manager"""
        async with self._session_factory() as session:
            async with transaction_context(session):
                yield session
    
    async def execute_in_transaction(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation within transaction"""
        async with self.transaction() as session:
            return await operation(session, *args, **kwargs)
```

## Repository Implementation Patterns

### Base Repository Pattern

```python
# infrastructure/database/repositories/base_repository.py
from abc import ABC
from typing import TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
import logging

logger = logging.getLogger(__name__)

TEntity = TypeVar('TEntity')
TModel = TypeVar('TModel')

class BaseRepository(ABC, Generic[TEntity, TModel]):
    """Base repository with common database operations"""
    
    def __init__(self, session: AsyncSession, model_class: type[TModel]):
        self._session = session
        self._model_class = model_class
    
    async def _execute_query(self, query):
        """Execute query with error handling"""
        try:
            result = await self._session.execute(query)
            return result
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            raise
    
    async def _commit(self):
        """Commit transaction"""
        try:
            await self._session.commit()
        except Exception as e:
            logger.error(f"Transaction commit failed: {str(e)}")
            raise
    
    async def exists_by_id(self, id: int) -> bool:
        """Check if entity exists by ID"""
        query = select(self._model_class).where(self._model_class.id == id)
        result = await self._execute_query(query)
        return result.scalar_one_or_none() is not None
```

### CRUD Repository Pattern

```python
# infrastructure/database/repositories/crud_repository.py
from typing import List, Optional, Any, Dict
from sqlalchemy import select, update, delete
from .base_repository import BaseRepository

class CrudRepository(BaseRepository[TEntity, TModel]):
    """Repository with standard CRUD operations"""
    
    async def get_by_id(self, id: int) -> Optional[TEntity]:
        """Get entity by ID"""
        query = select(self._model_class).where(self._model_class.id == id)
        result = await self._execute_query(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_all(self) -> List[TEntity]:
        """Get all entities"""
        query = select(self._model_class)
        result = await self._execute_query(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def create(self, entity: TEntity) -> TEntity:
        """Create new entity"""
        model = self._to_model(entity)
        self._session.add(model)
        await self._commit()
        await self._session.refresh(model)
        return self._to_entity(model)
    
    async def update(self, entity: TEntity) -> TEntity:
        """Update existing entity"""
        if not hasattr(entity, 'id') or not entity.id:
            raise ValueError("Entity must have an ID to be updated")
        
        model = self._to_model(entity)
        update_data = self._get_update_data(entity)
        
        query = (
            update(self._model_class)
            .where(self._model_class.id == entity.id)
            .values(**update_data)
        )
        
        await self._execute_query(query)
        await self._commit()
        
        # Return updated entity
        return await self.get_by_id(entity.id)
    
    async def delete(self, id: int) -> bool:
        """Delete entity by ID"""
        query = delete(self._model_class).where(self._model_class.id == id)
        result = await self._execute_query(query)
        await self._commit()
        return result.rowcount > 0
    
    def _to_entity(self, model: TModel) -> TEntity:
        """Convert database model to domain entity"""
        raise NotImplementedError
    
    def _to_model(self, entity: TEntity) -> TModel:
        """Convert domain entity to database model"""
        raise NotImplementedError
    
    def _get_update_data(self, entity: TEntity) -> Dict[str, Any]:
        """Get data for update operations"""
        raise NotImplementedError
```

## Query Optimization Patterns

### Pagination Pattern

```python
# infrastructure/database/repositories/pagination_repository.py
from typing import List, Tuple
from sqlalchemy import select, func
from math import ceil

class PaginatedRepository(BaseRepository):
    """Repository with pagination support"""
    
    async def get_paginated(self, 
                          page: int = 1, 
                          page_size: int = 20,
                          filters: dict = None) -> Tuple[List[TEntity], int, int]:
        """
        Get paginated results
        Returns: (items, total_count, total_pages)
        """
        # Build base query
        query = select(self._model_class)
        if filters:
            query = self._apply_filters(query, filters)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = await self._session.scalar(count_query)
        
        # Apply pagination
        offset = (page - 1) * page_size
        paginated_query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self._session.execute(paginated_query)
        models = result.scalars().all()
        
        # Convert to entities
        entities = [self._to_entity(model) for model in models]
        total_pages = ceil(total_count / page_size) if total_count > 0 else 0
        
        return entities, total_count, total_pages
    
    def _apply_filters(self, query, filters: dict):
        """Apply filters to query"""
        for field, value in filters.items():
            if hasattr(self._model_class, field):
                query = query.where(getattr(self._model_class, field) == value)
        return query
```

### Query Builder Pattern

```python
# infrastructure/database/repositories/query_builder_repository.py
from typing import List, Any
from sqlalchemy import select, and_, or_, not_

class QueryBuilderRepository(BaseRepository):
    """Repository with advanced query building capabilities"""
    
    def create_query(self):
        """Create a new query builder"""
        return QueryBuilder(self._model_class)
    
    async def execute_query(self, query_builder) -> List[TEntity]:
        """Execute query builder and return entities"""
        query = query_builder.build()
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

class QueryBuilder:
    """Fluent query builder"""
    
    def __init__(self, model_class):
        self._model_class = model_class
        self._conditions = []
        self._order_by = []
        self._limit_value = None
        self._offset_value = None
    
    def where(self, condition):
        """Add WHERE condition"""
        self._conditions.append(condition)
        return self
    
    def where_equal(self, field: str, value: Any):
        """Add equality condition"""
        self._conditions.append(getattr(self._model_class, field) == value)
        return self
    
    def where_in(self, field: str, values: List[Any]):
        """Add IN condition"""
        self._conditions.append(getattr(self._model_class, field).in_(values))
        return self
    
    def order_by(self, field: str, ascending: bool = True):
        """Add ORDER BY clause"""
        column = getattr(self._model_class, field)
        self._order_by.append(column.asc() if ascending else column.desc())
        return self
    
    def limit(self, value: int):
        """Add LIMIT clause"""
        self._limit_value = value
        return self
    
    def offset(self, value: int):
        """Add OFFSET clause"""
        self._offset_value = value
        return self
    
    def build(self):
        """Build the final SQLAlchemy query"""
        query = select(self._model_class)
        
        if self._conditions:
            query = query.where(and_(*self._conditions))
        
        if self._order_by:
            query = query.order_by(*self._order_by)
        
        if self._limit_value:
            query = query.limit(self._limit_value)
        
        if self._offset_value:
            query = query.offset(self._offset_value)
        
        return query

# Usage example
async def get_active_tenants(self):
    """Get active tenants using query builder"""
    query = (self.create_query()
             .where_equal('is_waitlist', False)
             .where_not_none('admission_date')
             .order_by('admission_date', ascending=False)
             .limit(100))
    
    return await self.execute_query(query)
```

## Data Mapping Patterns

### Entity-Model Mapping Pattern

```python
# infrastructure/database/repositories/mappers/tenant_mapper.py
from domain.entities.tenant_entity import TenantEntity
from models.models import Tenant as TenantModel
from datetime import datetime

class TenantMapper:
    """Maps between Tenant entities and models"""
    
    @staticmethod
    def to_entity(model: TenantModel) -> TenantEntity:
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
    
    @staticmethod
    def to_model(entity: TenantEntity) -> TenantModel:
        """Convert domain entity to database model"""
        return TenantModel(
            id=entity.id,
            created_at=entity.created_at,
            name=entity.name,
            admission_date=entity.admission_date,
            discharge_date=entity.discharge_date,
            waitlist=entity.is_waitlist,
            organization_id=entity.organization_id
        )
    
    @staticmethod
    def to_update_dict(entity: TenantEntity) -> dict:
        """Convert entity to dictionary for updates"""
        return {
            'name': entity.name,
            'admission_date': entity.admission_date,
            'discharge_date': entity.discharge_date,
            'waitlist': entity.is_waitlist,
            'organization_id': entity.organization_id
        }

# Usage in repository
class SQLTenantRepository(TenantRepository):
    """Repository using mapper for conversions"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = TenantMapper()
    
    def _to_entity(self, model: TenantModel) -> TenantEntity:
        return self._mapper.to_entity(model)
    
    def _to_model(self, entity: TenantEntity) -> TenantModel:
        return self._mapper.to_model(entity)
```

### Bulk Operations Pattern

```python
# infrastructure/database/repositories/bulk_repository.py
from typing import List
from sqlalchemy import insert, update, delete

class BulkRepository(BaseRepository):
    """Repository with bulk operation support"""
    
    async def bulk_create(self, entities: List[TEntity]) -> List[TEntity]:
        """Create multiple entities efficiently"""
        if not entities:
            return []
        
        # Convert entities to dictionaries
        data = [self._entity_to_dict(entity) for entity in entities]
        
        # Bulk insert
        stmt = insert(self._model_class).values(data)
        await self._session.execute(stmt)
        await self._session.commit()
        
        # Return created entities (may need to fetch IDs)
        return await self._get_created_entities(entities)
    
    async def bulk_update(self, entities: List[TEntity]) -> List[TEntity]:
        """Update multiple entities efficiently"""
        if not entities:
            return []
        
        # Group by ID for efficient updates
        for entity in entities:
            update_data = self._entity_to_dict(entity)
            stmt = (
                update(self._model_class)
                .where(self._model_class.id == entity.id)
                .values(**update_data)
            )
            await self._session.execute(stmt)
        
        await self._session.commit()
        
        # Return updated entities
        return [await self.get_by_id(entity.id) for entity in entities]
    
    def _entity_to_dict(self, entity: TEntity) -> dict:
        """Convert entity to dictionary for bulk operations"""
        raise NotImplementedError
```

## Error Handling Patterns

### Database Exception Handling

```python
# infrastructure/database/exceptions.py
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
import logging

logger = logging.getLogger(__name__)

class DatabaseException(Exception):
    """Base database exception"""
    pass

class DuplicateKeyError(DatabaseException):
    """Raised when unique constraint is violated"""
    pass

class ConnectionError(DatabaseException):
    """Raised when database connection fails"""
    pass

class QueryError(DatabaseException):
    """Raised when query execution fails"""
    pass

def handle_database_exceptions(func):
    """Decorator to handle database exceptions"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Integrity error: {str(e)}")
            raise DuplicateKeyError("Data integrity violation") from e
        except OperationalError as e:
            logger.error(f"Operational error: {str(e)}")
            raise ConnectionError("Database operation failed") from e
        except ProgrammingError as e:
            logger.error(f"Programming error: {str(e)}")
            raise QueryError("Invalid database query") from e
        except Exception as e:
            logger.error(f"Unexpected database error: {str(e)}")
            raise DatabaseException("Database operation failed") from e
    
    return wrapper
```

## Performance Patterns

### Connection Pool Monitoring

```python
# infrastructure/database/monitoring.py
from sqlalchemy import event
import logging
import time

logger = logging.getLogger(__name__)

class DatabaseMonitor:
    """Monitor database connection pool and performance"""
    
    def __init__(self, engine):
        self._engine = engine
        self._setup_monitoring()
    
    def _setup_monitoring(self):
        """Set up SQLAlchemy event listeners"""
        
        @event.listens_for(self._engine, "connect")
        def connect_event(dbapi_connection, connection_record):
            logger.info("Database connection established")
        
        @event.listens_for(self._engine, "close")
        def close_event(dbapi_connection, connection_record):
            logger.info("Database connection closed")
        
        @event.listens_for(self._engine, "checkout")
        def checkout_event(dbapi_connection, connection_record, connection_proxy):
            logger.debug("Database connection checked out from pool")
        
        @event.listens_for(self._engine, "checkin")
        def checkin_event(dbapi_connection, connection_record, connection_proxy):
            logger.debug("Database connection returned to pool")
    
    async def get_pool_status(self) -> dict:
        """Get current connection pool status"""
        pool = self._engine.pool
        return {
            'pool_size': pool.size(),
            'checked_out': pool.checkedout(),
            'available': pool.size() - pool.checkedout(),
            'invalid': pool.invalid(),
            'overflow': getattr(pool, '_overflow', 0)
        }
```

### Query Performance Monitoring

```python
# infrastructure/database/query_monitor.py
import time
from sqlalchemy import event
import logging

logger = logging.getLogger(__name__)

class QueryPerformanceMonitor:
    """Monitor query performance"""
    
    def __init__(self, slow_query_threshold: float = 1.0):
        self._slow_query_threshold = slow_query_threshold
        self._query_start_time = {}
    
    def setup_monitoring(self, engine):
        """Set up query performance monitoring"""
        
        @event.listens_for(engine, "before_execute")
        def before_execute(conn, clauseelement, multiparams, params):
            self._query_start_time[id(conn)] = time.time()
        
        @event.listens_for(engine, "after_execute")
        def after_execute(conn, clauseelement, multiparams, params, result):
            start_time = self._query_start_time.pop(id(conn), None)
            if start_time:
                duration = time.time() - start_time
                query_str = str(clauseelement).strip()
                
                if duration > self._slow_query_threshold:
                    logger.warning(".3f")
                else:
                    logger.debug(".3f")
```

## Migration Patterns

### Schema Migration Pattern

```python
# infrastructure/database/migrations/migration_001_add_tenant_table.py
from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func

def upgrade(metadata: MetaData):
    """Create tenant table"""
    tenant_table = Table(
        'tenants',
        metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('created_at', DateTime, nullable=False, server_default=func.now()),
        Column('name', String(100), nullable=False),
        Column('admission_date', DateTime, nullable=True),
        Column('discharge_date', DateTime, nullable=True),
        Column('waitlist', Boolean, nullable=False, default=True),
        Column('organization_id', Integer, ForeignKey('organizations.id'), nullable=False),
    )
    
    tenant_table.create()

def downgrade(metadata: MetaData):
    """Drop tenant table"""
    metadata.tables['tenants'].drop()
```

### Data Migration Pattern

```python
# infrastructure/database/migrations/migration_002_migrate_tenant_data.py
async def data_migration(session: AsyncSession):
    """Migrate existing tenant data"""
    
    # Get all tenants
    stmt = select(TenantModel)
    result = await session.execute(stmt)
    tenants = result.scalars().all()
    
    # Apply data transformations
    for tenant in tenants:
        # Example: Set default values for new columns
        if tenant.admission_date is None and not tenant.waitlist:
            tenant.admission_date = tenant.created_at
        
        # Example: Data validation and cleanup
        tenant.name = tenant.name.strip().title()
    
    await session.commit()
```

## Testing Patterns

### Repository Integration Testing

```python
# tests/integration/test_tenant_repository.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.database.repositories.sql_tenant_repository import SQLTenantRepository
from domain.entities.tenant_entity import TenantEntity

@pytest.mark.asyncio
async def test_tenant_repository_integration(db_session: AsyncSession):
    """Integration test for tenant repository"""
    repository = SQLTenantRepository(db_session)
    
    # Test create
    tenant = TenantEntity.create_tenant("Integration Test", 1)
    created = await repository.create(tenant)
    
    assert created.id is not None
    assert created.name == "Integration Test"
    
    # Test retrieve
    retrieved = await repository.get_by_id(created.id)
    assert retrieved.name == "Integration Test"
    
    # Test update
    retrieved.name = "Updated Test"
    updated = await repository.update(retrieved)
    assert updated.name == "Updated Test"
    
    # Test delete
    deleted = await repository.delete(created.id)
    assert deleted == True
    
    # Verify deletion
    not_found = await repository.get_by_id(created.id)
    assert not_found is None
```

### Database Transaction Testing

```python
# tests/integration/test_transaction_management.py
import pytest
from infrastructure.database.transaction import TransactionManager
from domain.entities.tenant_entity import TenantEntity

@pytest.mark.asyncio
async def test_transaction_rollback_on_failure(db_session_factory):
    """Test that transactions rollback on failure"""
    transaction_manager = TransactionManager(db_session_factory)
    
    with pytest.raises(ValueError):
        async with transaction_manager.transaction() as session:
            repository = SQLTenantRepository(session)
            
            # Create a tenant
            tenant = TenantEntity.create_tenant("Test", 1)
            await repository.create(tenant)
            
            # Force a failure
            raise ValueError("Simulated failure")
    
    # Verify rollback - tenant should not exist
    # (This would require a fresh session to verify)
```

This pattern ensures robust, performant, and maintainable database integration while keeping the domain layer clean and focused on business logic.
