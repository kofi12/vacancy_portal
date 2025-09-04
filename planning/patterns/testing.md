# 🧪 Testing Patterns in Clean Architecture

## Overview

Clean Architecture enables comprehensive testing at each layer with clear separation of concerns.

## Testing Pyramid

End-to-End Tests (Few)
↕️
Integration Tests (Some)
↕️
Unit Tests (Many)
↕️
Domain Layer (Core Business Logic)

## Domain Layer Testing

### Entity Testing Patterns

```python
# tests/domain/test_tenant_entity.py
import pytest
from datetime import datetime, timedelta
from domain.entities.tenant_entity import TenantEntity

class TestTenantEntity:
    
    def test_tenant_creation_success(self):
        """Test successful tenant creation"""
        tenant = TenantEntity.create_tenant("John Doe", 1, is_waitlist=True)
        
        assert tenant.name == "John Doe"
        assert tenant.organization_id == 1
        assert tenant.is_waitlist == True
        assert tenant.admission_date is None
    
    def test_tenant_creation_validation(self):
        """Test tenant creation validation"""
        with pytest.raises(ValueError, match="Tenant name cannot be empty"):
            TenantEntity.create_tenant("", 1)
        
        with pytest.raises(ValueError, match="Valid organization ID required"):
            TenantEntity.create_tenant("John Doe", 0)
    
    def test_admission_business_logic(self):
        """Test tenant admission business rules"""
        tenant = TenantEntity.create_tenant("Jane Doe", 1, is_waitlist=True)
        
        # Can be admitted when on waitlist and not admitted
        assert tenant.can_be_admitted() == True
        
        # Admit tenant
        admission_date = datetime.utcnow()
        tenant.admit(admission_date)
        
        # Now cannot be admitted again
        assert tenant.can_be_admitted() == False
        assert tenant.is_currently_admitted() == True
    
    def test_discharge_business_logic(self):
        """Test tenant discharge business rules"""
        tenant = TenantEntity.create_tenant("Jane Doe", 1, is_waitlist=True)
        admission_date = datetime.utcnow()
        discharge_date = admission_date + timedelta(days=30)
        
        # Cannot discharge before admission
        assert tenant.can_be_discharged() == False
        
        # Admit then discharge
        tenant.admit(admission_date)
        assert tenant.can_be_discharged() == True
        
        tenant.discharge(discharge_date)
        assert tenant.can_be_discharged() == False
        assert tenant.is_currently_admitted() == False
```

### Domain Service Testing

```python
# tests/domain/test_tenant_service.py
import pytest
from unittest.mock import AsyncMock
from domain.services.tenant_service import TenantService
from domain.entities.tenant_entity import TenantEntity

@pytest.fixture
def mock_repository():
    return AsyncMock()

@pytest.fixture
def tenant_service(mock_repository):
    return TenantService(mock_repository)

@pytest.mark.asyncio
class TestTenantService:
    
    async def test_create_tenant_success(self, tenant_service, mock_repository):
        """Test successful tenant creation"""
        # Arrange
        tenant = TenantEntity.create_tenant("Test Tenant", 1)
        mock_repository.exists_by_name.return_value = False
        mock_repository.create.return_value = tenant
        
        # Act
        result = await tenant_service.create_tenant(tenant)
        
        # Assert
        assert result.name == "Test Tenant"
        mock_repository.create.assert_called_once_with(tenant)
    
    async def test_create_tenant_duplicate_name(self, tenant_service, mock_repository):
        """Test tenant creation with duplicate name"""
        # Arrange
        tenant = TenantEntity.create_tenant("Duplicate Name", 1)
        mock_repository.exists_by_name.return_value = True
        
        # Act & Assert
        with pytest.raises(TenantAlreadyExistsError, 
                          match="Tenant 'Duplicate Name' already exists"):
            await tenant_service.create_tenant(tenant)
        
        # Verify create was not called
        mock_repository.create.assert_not_called()
    
    async def test_admit_tenant_success(self, tenant_service, mock_repository):
        """Test successful tenant admission"""
        # Arrange
        tenant = TenantEntity.create_tenant("Test", 1, is_waitlist=True)
        mock_repository.get_by_id.return_value = tenant
        mock_repository.update.return_value = tenant
        
        admission_date = datetime.utcnow()
        
        # Act
        result = await tenant_service.admit_tenant(1, admission_date)
        
        # Assert
        assert result.is_currently_admitted() == True
        mock_repository.update.assert_called_once()
```

## Application Layer Testing

### Use Case Testing

```python
# tests/application/use_cases/test_create_tenant_use_case.py
import pytest
from unittest.mock import AsyncMock
from application.use_cases.create_tenant_use_case import CreateTenantUseCase
from application.dto.tenant_dto import CreateTenantRequest

@pytest.fixture
def mock_tenant_service():
    return AsyncMock()

@pytest.fixture
def create_tenant_use_case(mock_tenant_service):
    return CreateTenantUseCase(mock_tenant_service)

@pytest.mark.asyncio
class TestCreateTenantUseCase:
    
    async def test_execute_success(self, create_tenant_use_case, mock_tenant_service):
        """Test successful use case execution"""
        # Arrange
        request = CreateTenantRequest(name="Test Tenant", organization_id=1)
        
        mock_created_tenant = AsyncMock()
        mock_created_tenant.id = 1
        mock_created_tenant.name = "Test Tenant"
        mock_tenant_service.create_tenant.return_value = mock_created_tenant
        
        # Act
        result = await create_tenant_use_case.execute(request)
        
        # Assert
        assert result.id == 1
        assert result.name == "Test Tenant"
        mock_tenant_service.create_tenant.assert_called_once()
    
    async def test_execute_with_validation_error(self, create_tenant_use_case):
        """Test use case with validation error"""
        # Arrange
        request = CreateTenantRequest(name="", organization_id=1)
        
        # Act & Assert
        with pytest.raises(ValidationError):
            await create_tenant_use_case.execute(request)
```

### DTO Testing

```python
# tests/application/dto/test_tenant_dto.py
import pytest
from datetime import datetime
from application.dto.tenant_dto import TenantResponse
from domain.entities.tenant_entity import TenantEntity

class TestTenantDTO:
    
    def test_tenant_response_from_entity(self):
        """Test DTO creation from domain entity"""
        # Arrange
        tenant = TenantEntity(
            id=1,
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            name="Test Tenant",
            admission_date=datetime(2023, 1, 2, 10, 0, 0),
            is_waitlist=False,
            organization_id=1
        )
        
        # Act
        response = TenantResponse.from_entity(tenant)
        
        # Assert
        assert response.id == 1
        assert response.name == "Test Tenant"
        assert response.admission_date == datetime(2023, 1, 2, 10, 0, 0)
        assert response.is_waitlist == False
        assert response.organization_id == 1
    
    def test_tenant_response_validation(self):
        """Test DTO validation"""
        # Valid DTO
        response = TenantResponse(
            id=1,
            name="Valid Name",
            organization_id=1
        )
        assert response.name == "Valid Name"
        
        # Invalid DTO - missing required field
        with pytest.raises(ValidationError):
            TenantResponse(organization_id=1)  # Missing name
```

## Infrastructure Layer Testing

### Repository Testing

```python
# tests/infrastructure/repositories/test_sql_tenant_repository.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.database.repositories.sql_tenant_repository import SQLTenantRepository
from domain.entities.tenant_entity import TenantEntity

@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def repository(mock_session):
    return SQLTenantRepository(mock_session)

@pytest.mark.asyncio
class TestSQLTenantRepository:
    
    async def test_get_by_id_success(self, repository, mock_session):
        """Test successful tenant retrieval"""
        # Arrange
        tenant_model = MagicMock()
        tenant_model.id = 1
        tenant_model.name = "Test Tenant"
        tenant_model.admission_date = None
        tenant_model.discharge_date = None
        tenant_model.waitlist = True
        tenant_model.organization_id = 1
        tenant_model.created_at = datetime.utcnow()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = tenant_model
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.get_by_id(1)
        
        # Assert
        assert result.id == 1
        assert result.name == "Test Tenant"
        assert result.is_waitlist == True
        mock_session.execute.assert_called_once()
    
    async def test_get_by_id_not_found(self, repository, mock_session):
        """Test tenant retrieval when not found"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.get_by_id(999)
        
        # Assert
        assert result is None
    
    async def test_create_tenant(self, repository, mock_session):
        """Test tenant creation"""
        # Arrange
        tenant = TenantEntity.create_tenant("New Tenant", 1)
        
        tenant_model = MagicMock()
        tenant_model.id = 1
        tenant_model.name = "New Tenant"
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        # Mock the _to_entity method to return the tenant
        repository._to_entity = MagicMock(return_value=tenant)
        
        # Act
        result = await repository.create(tenant)
        
        # Assert
        assert result.name == "New Tenant"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
```

### Integration Testing

```python
# tests/integration/test_tenant_creation_workflow.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from application.use_cases.create_tenant_use_case import CreateTenantUseCase
from application.dto.tenant_dto import CreateTenantRequest
from domain.services.tenant_service import TenantService
from infrastructure.database.repositories.sql_tenant_repository import SQLTenantRepository

@pytest.mark.asyncio
async def test_tenant_creation_workflow(db_session: AsyncSession):
    """Integration test for complete tenant creation workflow"""
    # Arrange
    repository = SQLTenantRepository(db_session)
    tenant_service = TenantService(repository)
    use_case = CreateTenantUseCase(tenant_service)
    
    request = CreateTenantRequest(
        name="Integration Test Tenant",
        organization_id=1
    )
    
    # Act
    result = await use_case.execute(request)
    
    # Assert
    assert result.name == "Integration Test Tenant"
    assert result.organization_id == 1
    assert result.id is not None
    
    # Verify in database
    retrieved = await repository.get_by_id(result.id)
    assert retrieved.name == "Integration Test Tenant"
```

## Presentation Layer Testing

### Controller Testing

```python
# tests/presentation/controllers/test_tenant_controller.py
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from presentation.controllers.tenant_controller import tenant_router
from application.use_cases.tenant_use_cases import AdmitTenantUseCase
from application.dto.tenant_dto import AdmitTenantRequest

@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(tenant_router)
    return app

@pytest.fixture
def client(test_app):
    return TestClient(test_app)

@pytest.fixture
def mock_admit_use_case():
    return AsyncMock(spec=AdmitTenantUseCase)

def test_admit_tenant_endpoint_success(client, mock_admit_use_case):
    """Test tenant admission endpoint"""
    # This would require proper dependency injection setup
    # For a complete example, see the controller testing patterns below
    pass
```

### Controller Testing with Dependency Override

```python
# tests/presentation/controllers/test_tenant_controller.py
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from presentation.controllers.tenant_controller import tenant_router, get_admit_tenant_use_case
from application.dto.tenant_dto import AdmitTenantRequest, TenantResponse

@pytest.fixture
def mock_use_case():
    use_case = AsyncMock()
    mock_response = TenantResponse(
        id=1,
        name="Test Tenant",
        admission_date=datetime.utcnow(),
        is_waitlist=False,
        organization_id=1
    )
    use_case.execute.return_value = mock_response
    return use_case

@pytest.fixture
def test_app(mock_use_case):
    app = FastAPI()
    app.include_router(tenant_router)
    
    # Override dependency
    app.dependency_overrides[get_admit_tenant_use_case] = lambda: mock_use_case
    
    return app

@pytest.fixture
def client(test_app):
    return TestClient(test_app)

def test_admit_tenant_endpoint(client, mock_use_case):
    """Test tenant admission endpoint"""
    request_data = {
        "tenant_id": 1,
        "admission_date": "2023-01-01T10:00:00Z"
    }
    
    response = client.post("/api/v2/tenants/1/admit", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Tenant"
    assert data["is_waitlist"] == False
    
    # Verify use case was called correctly
    mock_use_case.execute.assert_called_once()
    call_args = mock_use_case.execute.call_args[0][0]
    assert call_args.tenant_id == 1
```

## End-to-End Testing

### API Testing

```python
# tests/e2e/test_tenant_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_complete_tenant_lifecycle(client):
    """Test complete tenant lifecycle through API"""
    # Create tenant
    create_response = client.post(
        "/api/v2/tenants",
        json={
            "name": "E2E Test Tenant",
            "organization_id": 1,
            "is_waitlist": True
        }
    )
    assert create_response.status_code == 200
    tenant_data = create_response.json()
    tenant_id = tenant_data["id"]
    
    # Admit tenant
    admit_response = client.post(
        f"/api/v2/tenants/{tenant_id}/admit",
        json={
            "admission_date": "2023-01-01T10:00:00Z"
        }
    )
    assert admit_response.status_code == 200
    
    # Verify admission
    get_response = client.get(f"/api/v2/tenants/{tenant_id}")
    assert get_response.status_code == 200
    updated_tenant = get_response.json()
    assert updated_tenant["is_waitlist"] == False
```

## Testing Best Practices

### 1. **Test Isolation**

```python
# ✅ Good: Isolated tests
def test_tenant_creation():
    tenant = TenantEntity.create_tenant("Test", 1)
    assert tenant.name == "Test"

# ❌ Bad: Tests depending on external state
def test_tenant_creation():
    # Depends on database state
    existing_count = db.query(Tenant).count()
    create_tenant_in_db("Test", 1)
    assert db.query(Tenant).count() == existing_count + 1
```

### 2. **Arrange-Act-Assert Pattern**

```python
def test_admit_tenant():
    # Arrange
    tenant = TenantEntity.create_tenant("Test", 1, is_waitlist=True)
    
    # Act
    tenant.admit(datetime.utcnow())
    
    # Assert
    assert tenant.is_currently_admitted() == True
    assert tenant.is_waitlist == False
```

### 3. **Descriptive Test Names**

```python
# ✅ Good: Descriptive names
def test_admit_tenant_fails_when_already_admitted():
    pass

def test_create_tenant_validates_name_required():
    pass

# ❌ Bad: Vague names
def test_admit():
    pass

def test_create():
    pass
```

### 4. **Test Data Builders**

```python
class TenantBuilder:
    """Test data builder for tenants"""
    
    def __init__(self):
        self._name = "Test Tenant"
        self._org_id = 1
        self._is_waitlist = False
    
    def with_name(self, name: str):
        self._name = name
        return self
    
    def in_organization(self, org_id: int):
        self._org_id = org_id
        return self
    
    def on_waitlist(self):
        self._is_waitlist = True
        return self
    
    def build(self) -> TenantEntity:
        return TenantEntity.create_tenant(
            self._name, self._org_id, is_waitlist=self._is_waitlist
        )

# Usage in tests
def test_tenant_admission():
    tenant = TenantBuilder().with_name("John").on_waitlist().build()
    tenant.admit(datetime.utcnow())
    assert tenant.is_currently_admitted() == True
```

### 5. **Parameterized Tests**

```python
@pytest.mark.parametrize("invalid_name", ["", "   ", None])
def test_create_tenant_rejects_invalid_names(invalid_name):
    """Test that create_tenant rejects various invalid names"""
    with pytest.raises(ValueError):
        TenantEntity.create_tenant(invalid_name, 1)

@pytest.mark.parametrize("org_id,expected_error", [
    (0, "Valid organization ID required"),
    (-1, "Valid organization ID required"),
    (None, "Valid organization ID required"),
])
def test_create_tenant_rejects_invalid_org_ids(org_id, expected_error):
    """Test that create_tenant rejects invalid organization IDs"""
    with pytest.raises(ValueError, match=expected_error):
        TenantEntity.create_tenant("Valid Name", org_id)
```

## Test Organization

### Directory Structure

tests/
├── domain/ # Domain layer tests
│ ├── entities/
│ └── services/
├── application/ # Application layer tests
│ ├── use_cases/
│ └── dto/
├── infrastructure/ # Infrastructure layer tests
│ ├── repositories/
│ └── container/
├── presentation/ # Presentation layer tests
│ └── controllers/
├── integration/ # Cross-layer tests
├── e2e/ # End-to-end tests
└── conftest.py # Shared fixtures

### Configuration

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Test database setup
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test_db"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Setup test data
        await setup_test_data(session)
        
        yield session
        
        # Cleanup
        await cleanup_test_data(session)

async def setup_test_data(session):
    """Setup test data"""
    # Create test organizations, etc.
    pass

async def cleanup_test_data(session):
    """Clean up test data"""
    # Clear test data
    pass
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: pytest --cov=src --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v2
```

This comprehensive testing strategy ensures each layer is thoroughly tested with appropriate testing patterns and tools.
