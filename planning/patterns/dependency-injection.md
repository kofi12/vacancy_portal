# 🔗 Dependency Injection Pattern

## Overview

Dependency Injection is a design pattern that allows objects to receive their dependencies from external sources rather than creating them internally.

## Key Characteristics

### ✅ Benefits

- **Testability**: Easy to mock dependencies in tests
- **Flexibility**: Can swap implementations without changing code
- **Maintainability**: Clear dependency relationships
- **Separation of Concerns**: Classes focus on their responsibilities

### ❌ Without Dependency Injection

```python
# ❌ Tight coupling - hard to test
class TenantService:
    def __init__(self):
        self._repository = SQLTenantRepository()  # Can't mock this
    
    async def create_tenant(self, tenant):
        return await self._repository.create(tenant)
```

### ✅ With Dependency Injection

```python
# ✅ Loose coupling - easy to test
class TenantService:
    def __init__(self, tenant_repository: TenantRepository):
        self._tenant_repository = tenant_repository  # Injected dependency
    
    async def create_tenant(self, tenant):
        return await self._tenant_repository.create(tenant)
```

## Dependency Injection Container

### Basic Container Setup

```python
# infrastructure/container.py
from dependency_injector import containers, providers
from domain.repositories.tenant_repository import TenantRepository
from domain.services.tenant_service import TenantService
from infrastructure.database.repositories.sql_tenant_repository import SQLTenantRepository

class Container(containers.DeclarativeContainer):
    """Dependency injection container"""
    
    # Infrastructure layer - concrete implementations
    tenant_repository = providers.Factory(SQLTenantRepository)
    
    # Domain layer - services with injected dependencies
    tenant_service = providers.Factory(
        TenantService,
        tenant_repository=tenant_repository
    )
    
    # Application layer - use cases with injected services
    create_tenant_use_case = providers.Factory(
        CreateTenantUseCase,
        tenant_service=tenant_service
    )

# Global container instance
container = Container()
```

### Wiring the Container

```python
# main.py
from infrastructure.container import container

# Wire the container to resolve dependencies
container.wire(modules=[__name__])

app = FastAPI()

# Dependencies are now automatically resolved
@app.post('/tenants')
async def create_tenant(
    request: CreateTenantRequest,
    use_case = Depends(container.create_tenant_use_case)
):
    return await use_case.execute(request)
```

## Dependency Patterns

### Constructor Injection

```python
# Most common pattern
class TenantService:
    def __init__(self, tenant_repository: TenantRepository):
        self._tenant_repository = tenant_repository

# Usage
service = TenantService(repository_instance)
```

### Method Injection

```python
class ReportGenerator:
    def generate_report(self, tenant_repository: TenantRepository):
        # Repository injected for this specific operation
        tenants = await tenant_repository.get_all()
        return self._create_report(tenants)

# Usage
generator = ReportGenerator()
report = await generator.generate_report(repository_instance)
```

### Property Injection

```python
class NotificationService:
    def __init__(self):
        self._email_sender = None
    
    @property
    def email_sender(self):
        return self._email_sender
    
    @email_sender.setter
    def email_sender(self, sender):
        self._email_sender = sender

# Usage
service = NotificationService()
service.email_sender = email_sender_instance
```

## Advanced Container Patterns

### Scoped Dependencies

```python
class Container(containers.DeclarativeContainer):
    """Container with scoped dependencies"""
    
    # Singleton - same instance across application
    config = providers.Singleton(AppConfig)
    
    # Factory - new instance each time
    tenant_service = providers.Factory(TenantService)
    
    # Thread-local storage
    db_session = providers.ThreadLocalSingleton(get_db_session)
    
    # Resource - managed lifecycle
    file_handler = providers.Resource(FileHandler.init_async)
```

### Environment-Specific Configurations

```python
class Container(containers.DeclarativeContainer):
    """Environment-aware container"""
    
    # Base configuration
    config = providers.Singleton(AppConfig)
    
    # Environment-specific repositories
    @providers.Singleton
    def tenant_repository(config):
        if config.environment == "test":
            return InMemoryTenantRepository()
        else:
            return SQLTenantRepository()
    
    # Services depend on repository (resolved at runtime)
    tenant_service = providers.Factory(
        TenantService,
        tenant_repository=tenant_repository
    )
```

### Async Dependencies

```python
class Container(containers.DeclarativeContainer):
    """Container with async dependencies"""
    
    # Async resource provider
    @providers.Resource
    async def db_engine():
        engine = create_async_engine(DATABASE_URL)
        await engine.start()  # Async initialization
        yield engine
        await engine.dispose()  # Async cleanup
    
    # Async session factory
    db_session = providers.Factory(get_async_session, engine=db_engine)
    
    # Repository with async session
    tenant_repository = providers.Factory(
        SQLTenantRepository,
        session=db_session
    )
```

## Testing with Dependency Injection

### Unit Testing Pattern

```python
import pytest
from unittest.mock import AsyncMock
from domain.services.tenant_service import TenantService

@pytest.fixture
def mock_repository():
    return AsyncMock()

@pytest.fixture
def tenant_service(mock_repository):
    return TenantService(mock_repository)

@pytest.mark.asyncio
async def test_create_tenant_success(tenant_service, mock_repository):
    """Test tenant creation with mocked repository"""
    # Arrange
    mock_tenant = AsyncMock()
    mock_repository.create.return_value = mock_tenant
    
    # Act
    result = await tenant_service.create_tenant(mock_tenant)
    
    # Assert
    assert result == mock_tenant
    mock_repository.create.assert_called_once_with(mock_tenant)
```

### Integration Testing Pattern

```python
@pytest.fixture
def test_container():
    """Test-specific container with mocks"""
    container = Container()
    
    # Override with test implementations
    container.tenant_repository.override(MockTenantRepository())
    container.db_session.override(MockSession())
    
    return container

@pytest.mark.asyncio
async def test_tenant_creation_workflow(test_container):
    """Integration test using container"""
    # Get service from container
    tenant_service = test_container.tenant_service()
    
    # Test complete workflow
    tenant = TenantEntity.create_tenant("Test", 1)
    result = await tenant_service.create_tenant(tenant)
    
    assert result.name == "Test"
```

### Container Testing

```python
def test_container_wiring():
    """Test that container wires dependencies correctly"""
    container = Container()
    
    # Test that we can resolve dependencies
    tenant_repo = container.tenant_repository()
    assert isinstance(tenant_repo, SQLTenantRepository)
    
    tenant_service = container.tenant_service()
    assert isinstance(tenant_service, TenantService)
    assert tenant_service._tenant_repository is tenant_repo
```

## Controller Dependency Injection

### FastAPI Dependency Pattern

```python
# infrastructure/dependencies.py
from infrastructure.container import container

def get_create_tenant_use_case():
    return container.create_tenant_use_case()

def get_tenant_service():
    return container.tenant_service()

# presentation/controllers/tenant_controller.py
@tenant_router.post('/tenants')
async def create_tenant(
    request: CreateTenantRequest,
    use_case = Depends(get_create_tenant_use_case)
):
    return await use_case.execute(request)
```

### Manual Dependency Resolution

```python
# For testing or simple cases
def create_tenant_endpoint(request: CreateTenantRequest):
    # Manually resolve dependencies
    repository = SQLTenantRepository(get_db_session())
    service = TenantService(repository)
    use_case = CreateTenantUseCase(service)
    
    return use_case.execute(request)
```

## Error Handling with DI

### Exception Handler Dependencies

```python
class ExceptionHandler:
    def __init__(self, logger, notification_service):
        self._logger = logger
        self._notification_service = notification_service
    
    async def handle_error(self, error, context):
        # Log error
        await self._logger.log_error(error, context)
        
        # Send notification
        await self._notification_service.notify_admin(error)
        
        # Return appropriate response
        return self._create_error_response(error)

# In container
exception_handler = providers.Factory(
    ExceptionHandler,
    logger=logger,
    notification_service=email_service
)
```

## Best Practices

### 1. **Interface Segregation**

```python
# ✅ Good: Specific interfaces
class TenantReadRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int): pass
    @abstractmethod
    async def get_by_organization(self, org_id: int): pass

class TenantWriteRepository(ABC):
    @abstractmethod
    async def create(self, tenant): pass
    @abstractmethod
    async def update(self, tenant): pass

# ❌ Bad: Single large interface
class TenantRepository(ABC):
    # Read methods...
    # Write methods...
    # Admin methods...
    # Reporting methods...
```

### 2. **Dependency Direction**

```python
# ✅ Good: Dependencies point inward
# Presentation -> Application -> Domain <- Infrastructure

# ❌ Bad: Dependencies point outward
# Domain -> Infrastructure (tight coupling)
```

### 3. **Container Organization**

```python
# ✅ Good: Organized by layer
class Container(containers.DeclarativeContainer):
    # Infrastructure
    db_session = providers.Resource(get_db_session)
    
    # Domain
    tenant_repository = providers.Factory(SQLTenantRepository)
    tenant_service = providers.Factory(TenantService)
    
    # Application
    create_tenant_use_case = providers.Factory(CreateTenantUseCase)

# ❌ Bad: Unorganized
class Container(containers.DeclarativeContainer):
    a = providers.Factory(SomeClass)
    b = providers.Factory(AnotherClass)
    c = providers.Singleton(Config)
    # No clear organization
```

### 4. **Factory Functions**

```python
# ✅ Good: Factory functions for complex setup
@providers.Factory
def create_complex_service(config, repository, logger):
    service = ComplexService(config)
    service.repository = repository
    service.logger = logger
    return service

# ❌ Bad: Complex setup in constructor
class ComplexService:
    def __init__(self, config, repository, logger):
        # Complex setup logic here
        pass
```

### 5. **Lifecycle Management**

```python
# ✅ Good: Proper resource management
@providers.Resource
async def create_database_connection():
    connection = await create_connection()
    yield connection
    await connection.close()

# ❌ Bad: No cleanup
database_connection = providers.Singleton(create_connection)
```

## Common Patterns

### Plugin Architecture

```python
class PluginContainer(containers.DeclarativeContainer):
    """Container that can load plugins dynamically"""
    
    # Core services
    tenant_service = providers.Factory(TenantService)
    
    # Plugin loading
    @providers.Singleton
    def plugins():
        plugins = []
        for plugin_name in settings.ACTIVE_PLUGINS:
            plugin = importlib.import_module(f"plugins.{plugin_name}")
            plugins.append(plugin.PluginClass())
        return plugins
    
    # Services with plugins
    notification_service = providers.Factory(
        NotificationService,
        plugins=plugins
    )
```

### Configuration-Driven Dependencies

```python
class Container(containers.DeclarativeContainer):
    """Configuration-driven container"""
    
    config = providers.Singleton(AppConfig)
    
    @providers.Factory
    def repository(config):
        if config.database_type == "postgres":
            return PostgreSQLTenantRepository(config.connection_string)
        elif config.database_type == "mysql":
            return MySQLTenantRepository(config.connection_string)
        else:
            return InMemoryTenantRepository()
    
    tenant_service = providers.Factory(
        TenantService,
        repository=repository
    )
```

This pattern ensures clean dependency management and enables the flexibility and testability that Clean Architecture requires.
