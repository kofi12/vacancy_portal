# 🐛 Troubleshooting Guide

## Overview

This guide helps you diagnose and resolve common issues when implementing Clean Architecture in the Vacancy Portal.

## 🔍 Quick Diagnosis

### 1. Check Your Environment

```bash
# Verify Python version
python --version  # Should be 3.8+

# Check dependencies
pip list | grep -E "(fastapi|pydantic|dependency-injector)"

# Verify project structure
find . -name "*.py" | head -20
```

### 2. Run Basic Tests

```bash
# Test imports
python -c "from domain.entities.tenant_entity import TenantEntity; print('Domain OK')"

# Test application layer
python -c "from application.dto.tenant_dto import CreateTenantRequest; print('Application OK')"

# Test infrastructure
python -c "from infrastructure.database.session import get_db_session; print('Infrastructure OK')"
```

## 🚨 Common Issues & Solutions

### Issue: "ModuleNotFoundError" for Domain/Infrastructure

**Symptoms:**

TypeError: 'Depends' object is not callable
AttributeError: module 'dependency_injector' has no attribute 'providers'

**Root Causes:**

1. Missing dependency-injector installation
2. Incorrect import
3. Container not wired

**Solutions:**

**Install dependency-injector:**

```bash
pip install dependency-injector
```

**Check Imports:**

```python
# Correct import
from dependency_injector import containers, providers

# Incorrect import (old version)
from dependency_injector import Container, Provider
```

**Wire Container:**

```python
# In main.py
from infrastructure.container import container

# This must be called BEFORE creating FastAPI app
container.wire(modules=[__name__])

app = FastAPI()
```

### Issue: Database Connection Errors

**Symptoms:**

OperationalError: (psycopg2.OperationalError) connection to server failed
asyncpg.exceptions.ConnectionDoesNotExistError

**Root Causes:**

1. Database not running
2. Wrong connection string
3. Missing database driver

**Solutions:**

**Check Database Status:**

```bash
# PostgreSQL
sudo systemctl status postgresql

# Or check if port is open
netstat -tlnp | grep 5432
```

**Verify Connection String:**

```python
# In .env file or environment
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/vacancy_portal

# Test connection
python -c "
import asyncpg
async def test():
    conn = await asyncpg.connect('postgresql://user:password@localhost/vacancy_portal')
    await conn.close()
    print('Connection OK')
import asyncio
asyncio.run(test())
"
```

**Install Database Driver:**

```bash
# For PostgreSQL async
pip install asyncpg

# For MySQL async
pip install aiomysql
```

### Issue: Pydantic Validation Errors

**Symptoms:**

ValidationError: 1 validation error for CreateTenantRequest
name
field required (type=value_error.missing)

**Root Causes:**

1. Missing required fields
2. Wrong data types
3. Invalid field values

**Solutions:**

**Check Request Data:**

```python
# Valid request
request = CreateTenantRequest(
    name="John Doe",          # Required string
    organization_id=1,        # Required int > 0
    is_waitlist=True          # Optional bool
)

# Invalid requests
CreateTenantRequest()                    # Missing required fields
CreateTenantRequest(name="", org_id=1)   # Empty name
CreateTenantRequest(name="John", org_id=0)  # Invalid org_id
```

**Validate API Requests:**

```python
# In controller - FastAPI handles this automatically
@app.post("/tenants")
async def create_tenant(request: CreateTenantRequest):
    # FastAPI validates automatically
    return await use_case.execute(request)
```

**Debug Validation Errors:**

```python
# Add debug logging
try:
    request = CreateTenantRequest(**data)
except ValidationError as e:
    print("Validation errors:", e.errors())
    raise
```

### Issue: Business Logic Not Working

**Symptoms:**

- Entities not behaving as expected
- Use cases returning wrong results
- Business rules not enforced

**Root Causes:**

1. Business logic in wrong layer
2. Missing validation
3. Incorrect method calls

**Solutions:**

**Verify Business Logic Location:**

```python
# ✅ Correct: Business logic in domain
@dataclass
class TenantEntity(BaseEntity):
    name: str
    is_waitlist: bool = False
    
    def can_be_admitted(self) -> bool:
        return self.is_waitlist and self.admission_date is None

# ❌ Wrong: Business logic in controller
@app.post("/tenants")
def create_tenant(request):
    # Don't put business logic here
    if request.name and request.org_id > 0:
        # Business logic should be in domain
        pass
```

**Test Business Logic:**

```python
# Test domain entities
def test_tenant_admission():
    tenant = TenantEntity.create_tenant("Test", 1, is_waitlist=True)
    
    # Test business rule
    assert tenant.can_be_admitted() == True
    
    # Test behavior
    tenant.admit(datetime.utcnow())
    assert tenant.is_waitlist == False
```

**Debug Use Cases:**

```python
# Add logging to use cases
class CreateTenantUseCase:
    async def execute(self, request):
        logger.info(f"Creating tenant: {request.name}")
        
        # Step-by-step debugging
        tenant = TenantEntity.create_tenant(...)
        logger.info(f"Created entity: {tenant}")
        
        result = await self._service.create_tenant(tenant)
        logger.info(f"Service result: {result}")
        
        return result
```

### Issue: HTTP Exceptions Not Mapped Correctly

**Symptoms:**

HTTPException: 500 Internal Server Error instead of 404 Not Found

**Root Causes:**

1. Exception handler not applied
2. Domain exceptions not caught
3. Wrong HTTP status codes

**Solutions:**

**Apply Exception Handler:**

```python
# ✅ Correct: Apply to controller methods
@tenant_router.get("/tenants/{tenant_id}")
@handle_domain_exceptions
async def get_tenant(tenant_id: int):
    return await use_case.execute(tenant_id)

# ❌ Wrong: Missing decorator
@tenant_router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: int):
    return await use_case.execute(tenant_id)
```

**Check Exception Mapping:**

```python
def handle_domain_exceptions(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TenantNotFoundError as e:
            raise HTTPException(404, str(e))  # ✅ Correct
        except Exception as e:
            raise HTTPException(500, "Internal error")  # ✅ Fallback
    return wrapper
```

**Verify Domain Exceptions:**

```python
# Make sure domain services raise domain exceptions
class TenantService:
    async def get_tenant(self, tenant_id: int):
        tenant = await self._repo.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")
        return tenant
```

### Issue: Test Failures

**Symptoms:**

FAILED tests/domain/test_tenant_entity.py::test_create_tenant - AssertionError

**Root Causes:**

1. Wrong test expectations
2. Missing test setup
3. Import issues in tests

**Solutions:**

**Check Test Setup:**

```python
# ✅ Correct test structure
def test_create_tenant_success():
    tenant = TenantEntity.create_tenant("Test", 1)
    assert tenant.name == "Test"
    assert tenant.organization_id == 1

# ❌ Wrong test expectations
def test_create_tenant_success():
    tenant = TenantEntity.create_tenant("Test", 1)
    assert tenant.id is not None  # ID is None for new entities
```

**Fix Import Issues:**

```python
# Add to test files
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**Debug Test Failures:**

```python
# Run with verbose output
pytest tests/domain/test_tenant_entity.py -v -s

# Run specific test
pytest tests/domain/test_tenant_entity.py::TestTenantEntity::test_create_tenant_success -v
```

### Issue: Performance Problems

**Symptoms:**

- Slow response times
- High memory usage
- Database connection pool exhausted

**Root Causes:**

1. N+1 query problems
2. Missing database indexes
3. Inefficient queries

**Solutions:**

**Fix N+1 Queries:**

```python
# ❌ Bad: N+1 queries
tenants = await tenant_repo.get_by_organization(org_id)
for tenant in tenants:
    org = await org_repo.get_by_id(tenant.organization_id)  # N queries

# ✅ Good: Single query with join
async def get_tenants_with_org(self, org_id: int):
    stmt = select(TenantModel, OrganizationModel).join(
        OrganizationModel,
        TenantModel.organization_id == OrganizationModel.id
    ).where(TenantModel.organization_id == org_id)
    
    result = await self._session.execute(stmt)
    return result.all()
```

**Add Database Indexes:**

```sql
-- Add indexes for common queries
CREATE INDEX idx_tenants_org_id ON tenants(organization_id);
CREATE INDEX idx_tenants_waitlist ON tenants(waitlist);
CREATE INDEX idx_tenants_name_org ON tenants(name, organization_id);
```

**Optimize Connection Pool:**

```python
# In database configuration
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,              # Base connections
    max_overflow=20,           # Additional connections
    pool_recycle=3600,         # Recycle every hour
    pool_pre_ping=True,        # Test connections
    echo=False                 # Disable logging in production
)
```

## 🛠️ Diagnostic Tools

### 1. Health Check Endpoint

```python
# Add to main.py
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "checks": {
            "database": await check_database(),
            "domain_layer": await check_domain_layer(),
            "application_layer": await check_application_layer(),
            "infrastructure": await check_infrastructure()
        }
    }

async def check_database():
    """Check database connectivity"""
    try:
        # Simple query to test connection
        await db_session.execute(text("SELECT 1"))
        return "healthy"
    except Exception as e:
        return f"unhealthy: {str(e)}"
```

### 2. Debug Logging

```python
# Add to main.py
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add request logging
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(".3f")
    
    return response
```

### 3. Configuration Validation

```python
# infrastructure/config.py
def validate_configuration():
    """Validate application configuration"""
    required_env_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'API_VERSION'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ConfigurationError(f"Missing environment variables: {missing_vars}")
    
    # Validate database URL format
    db_url = os.getenv('DATABASE_URL')
    if not db_url.startswith(('postgresql', 'mysql', 'sqlite')):
        raise ConfigurationError("Invalid DATABASE_URL format")
```

## 📞 Getting Help

### 1. Check Documentation First

- [Architecture Overview](../01-architecture-overview.md)
- [Quick Start Guide](../02-quick-start.md)
- [Domain Layer Guide](../phases/01-domain-layer.md)
- [Application Layer Guide](../phases/02-application-layer.md)
- [Infrastructure Layer Guide](../phases/03-infrastructure-layer.md)
- [Presentation Layer Guide](../phases/04-presentation-layer.md)

### 2. Common Solutions

- **Restart your application** after configuration changes
- **Clear Python cache** if import issues persist: `find . -name "*.pyc" -delete`
- **Check file permissions** for database files
- **Verify environment variables** are set correctly

### 3. Debug Checklist

- [ ] Python version 3.8+
- [ ] All dependencies installed
- [ ] Database running and accessible
- [ ] Environment variables set
- [ ] File permissions correct
- [ ] No syntax errors in code
- [ ] All required `__init__.py` files present
- [ ] Container properly wired

### 4. When to Ask for Help

- You've tried the solutions above
- Error messages are unclear
- Problem persists after restart
- You're blocked and can't proceed

Include this information when asking for help:

- **Error message** (full traceback)
- **Steps to reproduce**
- **Your environment** (OS, Python version, dependencies)
- **Recent changes** that might have caused the issue
- **Full configuration** (without sensitive data)

This troubleshooting guide should resolve 90% of common issues. For the remaining 10%, the debug information above will help get you the right assistance.
