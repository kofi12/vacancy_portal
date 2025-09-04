# 🧪 Controller Testing Pattern

## Overview

Controller testing patterns ensure that HTTP endpoints work correctly while maintaining separation between HTTP concerns and business logic.

## Unit Testing Controllers

### Basic Controller Test Setup

```python
# tests/presentation/controllers/test_tenant_controller.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from presentation.controllers.tenant_controller import tenant_router
from application.use_cases.tenant_use_cases import CreateTenantUseCase
from application.dto.tenant_dto import CreateTenantRequest, TenantResponse
from domain.entities.tenant_entity import TenantEntity

@pytest.fixture
def mock_create_use_case():
    """Mock create tenant use case"""
    use_case = AsyncMock(spec=CreateTenantUseCase)
    
    # Mock successful creation
    mock_tenant = TenantEntity(
        id=1, name="Test Tenant", organization_id=1,
        created_at=datetime(2023, 1, 1)
    )
    mock_response = TenantResponse.from_entity(mock_tenant)
    use_case.execute.return_value = mock_response
    
    return use_case

@pytest.fixture
def test_app(mock_create_use_case):
    """Test FastAPI application with mocked dependencies"""
    app = FastAPI()
    app.include_router(tenant_router)
    
    # Override dependency injection
    app.dependency_overrides[CreateTenantUseCase] = lambda: mock_create_use_case
    
    return app

@pytest.fixture
def client(test_app):
    """Test client"""
    return TestClient(test_app)
```

### Happy Path Testing

```python
def test_create_tenant_success(client, mock_create_use_case):
    """Test successful tenant creation"""
    request_data = {
        "name": "John Doe",
        "organization_id": 1,
        "is_waitlist": True
    }
    
    response = client.post("/api/v2/tenants", json=request_data)
    
    # Assert HTTP response
    assert response.status_code == 201
    response_data = response.json()
    
    # Assert response structure
    assert response_data["id"] == 1
    assert response_data["name"] == "Test Tenant"
    assert response_data["organization_id"] == 1
    assert response_data["is_waitlist"] == False  # Mock data
    
    # Assert use case was called correctly
    mock_create_use_case.execute.assert_called_once()
    call_args = mock_create_use_case.execute.call_args[0][0]
    assert call_args.name == "John Doe"
    assert call_args.organization_id == 1
    assert call_args.is_waitlist == True
```

### Error Handling Testing

```python
def test_create_tenant_validation_error(client):
    """Test tenant creation with validation error"""
    # Invalid request - empty name
    request_data = {
        "name": "",  # Invalid
        "organization_id": 1
    }
    
    response = client.post("/api/v2/tenants", json=request_data)
    
    # Assert validation error
    assert response.status_code == 422
    error_data = response.json()
    
    # Check Pydantic validation error structure
    assert "detail" in error_data
    assert any(
        error["loc"] == ["body", "name"] 
        for error in error_data["detail"]
    )

def test_create_tenant_domain_error(client, mock_create_use_case):
    """Test tenant creation with domain error"""
    # Mock domain error (e.g., tenant already exists)
    from domain.exceptions.tenant_exceptions import TenantAlreadyExistsError
    mock_create_use_case.execute.side_effect = TenantAlreadyExistsError(
        tenant_name="John Doe", organization_id=1
    )
    
    request_data = {
        "name": "John Doe",
        "organization_id": 1
    }
    
    response = client.post("/api/v2/tenants", json=request_data)
    
    # Assert domain error handling
    assert response.status_code == 409  # Conflict
    error_data = response.json()
    
    assert error_data["error_code"] == "TENANT_ALREADY_EXISTS"
    assert "already exists" in error_data["message"]
    assert error_data["details"]["tenant_name"] == "John Doe"
```

### Path Parameter Testing

```python
def test_get_tenant_by_id_success(client, mock_get_use_case):
    """Test getting tenant by ID"""
    # Setup mock
    mock_tenant = TenantEntity(
        id=123, name="Test Tenant", organization_id=1,
        created_at=datetime(2023, 1, 1)
    )
    mock_response = TenantResponse.from_entity(mock_tenant)
    mock_get_use_case.execute.return_value = mock_response
    
    # Test request
    response = client.get("/api/v2/tenants/123")
    
    # Assert response
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 123
    assert response_data["name"] == "Test Tenant"
    
    # Assert use case called with correct ID
    mock_get_use_case.execute.assert_called_once_with(123)

def test_get_tenant_not_found(client, mock_get_use_case):
    """Test getting non-existent tenant"""
    # Mock not found
    mock_get_use_case.execute.return_value = None
    
    response = client.get("/api/v2/tenants/999")
    
    # Assert not found error
    assert response.status_code == 404
    error_data = response.json()
    assert error_data["error_code"] == "TENANT_NOT_FOUND"
    assert error_data["details"]["tenant_id"] == 999
```

## Integration Testing

### Full Request Flow Testing

```python
# tests/integration/test_tenant_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from main import app

@pytest.fixture
def client():
    """Test client with full application"""
    return TestClient(app)

@pytest.mark.asyncio
async def test_tenant_creation_integration(client, db_session: AsyncSession):
    """Integration test for complete tenant creation flow"""
    request_data = {
        "name": "Integration Test Tenant",
        "organization_id": 1,
        "is_waitlist": True
    }
    
    # Create tenant
    response = client.post("/api/v2/tenants", json=request_data)
    
    # Assert creation
    assert response.status_code == 201
    tenant_data = response.json()
    assert tenant_data["name"] == "Integration Test Tenant"
    assert "id" in tenant_data
    
    tenant_id = tenant_data["id"]
    
    # Retrieve tenant
    get_response = client.get(f"/api/v2/tenants/{tenant_id}")
    assert get_response.status_code == 200
    retrieved_data = get_response.json()
    assert retrieved_data["id"] == tenant_id
    assert retrieved_data["name"] == "Integration Test Tenant"
    
    # Admit tenant
    admit_response = client.post(
        f"/api/v2/tenants/{tenant_id}/admit",
        json={"admission_date": "2023-01-01T10:00:00Z"}
    )
    assert admit_response.status_code == 200
    admitted_data = admit_response.json()
    assert admitted_data["is_waitlist"] == False
```

### Authentication Testing

```python
def test_create_tenant_unauthorized(client):
    """Test tenant creation without authentication"""
    request_data = {
        "name": "Unauthorized Tenant",
        "organization_id": 1
    }
    
    # No Authorization header
    response = client.post("/api/v2/tenants", json=request_data)
    
    assert response.status_code == 401
    error_data = response.json()
    assert "authentication" in error_data["message"].lower()

def test_create_tenant_forbidden(client):
    """Test tenant creation with insufficient permissions"""
    request_data = {
        "name": "Forbidden Tenant", 
        "organization_id": 1
    }
    
    # Mock insufficient permissions
    response = client.post(
        "/api/v2/tenants", 
        json=request_data,
        headers={"Authorization": "Bearer insufficient-permissions-token"}
    )
    
    assert response.status_code == 403
    error_data = response.json()
    assert "authorization" in error_data["error_code"]
```

## Advanced Testing Patterns

### Data-Driven Testing

```python
@pytest.mark.parametrize("request_data,expected_status,expected_error", [
    # Valid request
    ({
        "name": "Valid Tenant",
        "organization_id": 1,
        "is_waitlist": True
    }, 201, None),
    
    # Invalid name
    ({
        "name": "",
        "organization_id": 1
    }, 422, "name"),
    
    # Invalid organization ID
    ({
        "name": "Valid Name",
        "organization_id": 0
    }, 422, "organization_id"),
    
    # Missing required field
    ({
        "organization_id": 1
    }, 422, "name"),
])
def test_create_tenant_validation_scenarios(client, request_data, expected_status, expected_error):
    """Test various validation scenarios"""
    response = client.post("/api/v2/tenants", json=request_data)
    
    assert response.status_code == expected_status
    
    if expected_error:
        error_data = response.json()
        assert any(
            expected_error in str(error)
            for error in error_data["detail"]
        )
```

### Mock Chain Testing

```python
def test_complex_workflow_with_mocks(client, mock_create_use_case, mock_admit_use_case):
    """Test complex workflow with multiple mocked dependencies"""
    # Setup create use case mock
    created_tenant = TenantEntity(
        id=1, name="Workflow Test", organization_id=1,
        created_at=datetime(2023, 1, 1)
    )
    mock_create_use_case.execute.return_value = TenantResponse.from_entity(created_tenant)
    
    # Setup admit use case mock
    admitted_tenant = created_tenant
    admitted_tenant.admit(datetime(2023, 1, 2))
    mock_admit_use_case.execute.return_value = TenantResponse.from_entity(admitted_tenant)
    
    # Test workflow endpoint
    workflow_request = {
        "name": "Workflow Test",
        "organization_id": 1,
        "is_waitlist": True,
        "admission_date": "2023-01-02T10:00:00Z"
    }
    
    response = client.post("/api/v2/tenant-management/workflows/admission", 
                          json=workflow_request)
    
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "Workflow Test"
    assert result["is_waitlist"] == False  # Should be admitted
    
    # Verify both use cases were called
    mock_create_use_case.execute.assert_called_once()
    mock_admit_use_case.execute.assert_called_once()
```

## Performance Testing

### Load Testing Controllers

```python
# tests/performance/test_tenant_controller_performance.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import requests

def test_tenant_creation_load(client):
    """Test tenant creation under load"""
    num_requests = 100
    concurrent_requests = 10
    
    def make_request(i):
        return client.post("/api/v2/tenants", json={
            "name": f"Load Test Tenant {i}",
            "organization_id": 1
        })
    
    start_time = time.time()
    
    # Execute requests concurrently
    with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        responses = list(executor.map(make_request, range(num_requests)))
    
    end_time = time.time()
    
    # Assert performance
    total_time = end_time - start_time
    avg_time = total_time / num_requests
    
    assert avg_time < 0.5  # Less than 500ms per request
    assert all(r.status_code == 201 for r in responses)
    
    print(f"Completed {num_requests} requests in {total_time:.2f}s")
    print(f"Average response time: {avg_time:.3f}s")
```

### Memory Leak Testing

```python
# tests/performance/test_memory_usage.py
import psutil
import os
from fastapi.testclient import TestClient

def test_memory_usage_under_load(client):
    """Test for memory leaks under sustained load"""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Perform many requests
    for i in range(1000):
        response = client.post("/api/v2/tenants", json={
            "name": f"Memory Test {i}",
            "organization_id": 1
        })
        assert response.status_code == 201
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # Allow some memory increase but not excessive
    assert memory_increase < 50  # Less than 50MB increase
    
    print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB")
    print(f"Increase: {memory_increase:.1f}MB")
```

## Security Testing

### Input Validation Testing

```python
def test_sql_injection_protection(client):
    """Test protection against SQL injection"""
    malicious_name = "'; DROP TABLE tenants; --"
    
    response = client.post("/api/v2/tenants", json={
        "name": malicious_name,
        "organization_id": 1
    })
    
    # Should either:
    # 1. Sanitize input and create successfully, or
    # 2. Reject malicious input
    assert response.status_code in [201, 422]
    
    if response.status_code == 201:
        # If created, verify the name was sanitized
        tenant_data = response.json()
        assert tenant_data["name"] != malicious_name  # Should be sanitized

def test_xss_protection(client):
    """Test protection against XSS attacks"""
    xss_payload = "<script>alert('XSS')</script>"
    
    response = client.post("/api/v2/tenants", json={
        "name": xss_payload,
        "organization_id": 1
    })
    
    if response.status_code == 201:
        tenant_data = response.json()
        # Ensure XSS payload is not in response
        assert "<script>" not in tenant_data["name"]
        assert "alert" not in tenant_data["name"]
```

### Rate Limiting Testing

```python
def test_rate_limiting(client):
    """Test rate limiting functionality"""
    # Make many requests quickly
    responses = []
    for i in range(60):  # More than typical rate limit
        response = client.post("/api/v2/tenants", json={
            "name": f"Rate Limit Test {i}",
            "organization_id": 1
        })
        responses.append(response)
    
    # Should have some successful and some rate limited
    success_count = sum(1 for r in responses if r.status_code == 201)
    rate_limited_count = sum(1 for r in responses if r.status_code == 429)
    
    assert success_count > 0  # Some should succeed
    assert rate_limited_count > 0  # Some should be rate limited
    
    print(f"Successful: {success_count}, Rate limited: {rate_limited_count}")
```

## Test Organization and Fixtures

### Shared Test Fixtures

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from main import app

@pytest.fixture(scope="session")
def test_engine():
    """Test database engine"""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost/test_db",
        echo=False
    )
    yield engine
    engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    """Test database session"""
    from sqlalchemy.orm import sessionmaker
    async_session = sessionmaker(test_engine, class_=AsyncSession)
    
    async with async_session() as session:
        yield session
        await session.rollback()  # Rollback changes after test

@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Authentication headers for tests"""
    return {"Authorization": "Bearer test-token"}

@pytest.fixture
def sample_tenant_data():
    """Sample tenant data for tests"""
    return {
        "name": "Test Tenant",
        "organization_id": 1,
        "is_waitlist": True
    }
```

### Test Data Builders

```python
# tests/builders/test_data_builder.py
from typing import Optional
from application.dto.tenant_dto import CreateTenantRequest
from domain.entities.tenant_entity import TenantEntity

class TenantRequestBuilder:
    """Builder for test tenant requests"""
    
    def __init__(self):
        self._name = "Test Tenant"
        self._organization_id = 1
        self._is_waitlist = False
    
    def with_name(self, name: str):
        self._name = name
        return self
    
    def in_organization(self, org_id: int):
        self._organization_id = org_id
        return self
    
    def on_waitlist(self):
        self._is_waitlist = True
        return self
    
    def build_request(self) -> CreateTenantRequest:
        """Build CreateTenantRequest"""
        return CreateTenantRequest(
            name=self._name,
            organization_id=self._organization_id,
            is_waitlist=self._is_waitlist
        )
    
    def build_entity(self) -> TenantEntity:
        """Build TenantEntity"""
        return TenantEntity.create_tenant(
            name=self._name,
            organization_id=self._organization_id,
            is_waitlist=self._is_waitlist
        )

# Usage in tests
def test_tenant_creation_with_builder(client):
    """Test using data builder"""
    request = (TenantRequestBuilder()
               .with_name("Builder Test")
               .on_waitlist()
               .build_request())
    
    response = client.post("/api/v2/tenants", json=request.model_dump())
    assert response.status_code == 201
```

This pattern ensures comprehensive testing of controllers while maintaining separation between HTTP concerns and business logic.
