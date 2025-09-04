# 🔄 Gradual Migration Strategy

## Overview

This guide shows how to migrate from your current architecture to Clean Architecture without breaking existing functionality.

## Migration Principles

### 🛡️ **Zero Breaking Changes**

- Existing API endpoints continue working
- Database schema remains unchanged
- Existing clients unaffected
- Rollback possible at any time

### 📊 **Incremental Progress**

- Migrate one feature at a time
- Each migration can be tested independently
- Gradual adoption over weeks/months
- Measure progress with metrics

### 🧪 **Safe Deployment**

- Feature flags for new functionality
- Parallel execution of old and new code
- Comprehensive testing at each step
- Monitoring and alerting

## Phase-by-Phase Migration Plan

### Phase 1: Foundation (Week 1)

**Goal:** Set up Clean Architecture foundation without changing functionality

#### Tasks

**Create Directory Structure*

```bash
mkdir -p domain/{entities,repositories,services,exceptions}
mkdir -p application/{use_cases,dto,interfaces}
mkdir -p infrastructure/{database,auth}
mkdir -p presentation/{controllers,middleware}
```

**Add Dependencies*

```toml
# pyproject.toml
[tool.poetry.dependencies]
dependency-injector = "^4.41.0"
pydantic = "^2.7.4"
```

**Create Base Classes*

- `domain/entities/base_entity.py`
- `application/dto/base_dto.py`
- `infrastructure/database/session.py`

#### Success Criteria

- ✅ All directories created
- ✅ Dependencies installed
- ✅ Base classes working
- ✅ Existing functionality unchanged

### Phase 2: Domain Layer (Week 2)

**Goal:** Extract business logic from existing code

#### Approach: Parallel Implementation

Keep existing DAOs working while building domain entities.

#### Step 1: Extract Simple Entity (Day 1-2)

```python
# Create domain/entities/tenant_entity.py
@dataclass
class TenantEntity(BaseEntity):
    name: str
    admission_date: Optional[datetime] = None
    is_waitlist: bool = False
    
    def can_be_admitted(self) -> bool:
        return self.is_waitlist and self.admission_date is None
```

#### Step 2: Create Repository Interface (Day 3-4)

```python
# Create domain/repositories/tenant_repository.py
class TenantRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[TenantEntity]:
        pass
```

#### Step 3: Create Domain Service (Day 5)

```python
# Create domain/services/tenant_service.py
class TenantService:
    def __init__(self, tenant_repository: TenantRepository):
        self._tenant_repository = tenant_repository
    
    async def admit_tenant(self, tenant_id: int, admission_date: datetime):
        tenant = await self._tenant_repository.get_by_id(tenant_id)
        if not tenant.can_be_admitted():
            raise ValueError("Cannot admit tenant")
        tenant.admit(admission_date)
        return await self._tenant_repository.update(tenant)
```

#### Testing Strategy

```python
# Test domain layer independently
def test_tenant_admission_business_logic():
    tenant = TenantEntity.create_tenant("Test", 1, is_waitlist=True)
    assert tenant.can_be_admitted() == True
    
    tenant.admit(datetime.utcnow())
    assert tenant.is_waitlist == False
```

### Phase 3: Application Layer (Week 3)

**Goal:** Create use cases and DTOs

#### Step 1: Create DTOs (Day 1-2)

```python
# Create application/dto/tenant_dto.py
class CreateTenantRequest(BaseDTO):
    name: str
    organization_id: int

class TenantResponse(BaseDTO):
    id: int
    name: str
    admission_date: Optional[datetime] = None
```

#### Step 2: Create Use Cases (Day 3-4)

```python
# Create application/use_cases/admit_tenant_use_case.py
class AdmitTenantUseCase:
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self, request: AdmitTenantRequest) -> TenantResponse:
        admitted_tenant = await self._tenant_service.admit_tenant(
            request.tenant_id, request.admission_date
        )
        return TenantResponse.from_entity(admitted_tenant)
```

#### Integration Testing

```python
# Test use case with mocked dependencies
def test_admit_tenant_use_case():
    # Mock repository and service
    mock_repo = MagicMock()
    mock_service = TenantService(mock_repo)
    use_case = AdmitTenantUseCase(mock_service)
    
    # Test execution
    request = AdmitTenantRequest(tenant_id=1, admission_date=datetime.utcnow())
    result = await use_case.execute(request)
    
    assert result.id == 1
```

### Phase 4: Infrastructure Layer (Week 4)

**Goal:** Implement concrete repositories and dependency injection

#### Step 1: Repository Implementation (Day 1-2)

```python
# Create infrastructure/database/repositories/sql_tenant_repository.py
class SQLTenantRepository(TenantRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, id: int) -> Optional[TenantEntity]:
        stmt = select(TenantModel).where(TenantModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
```

#### Step 2: Dependency Injection Setup (Day 3-4)

```python
# Create infrastructure/container.py
class Container(containers.DeclarativeContainer):
    db_session = providers.Resource(get_db_session)
    
    tenant_repository = providers.Factory(
        SQLTenantRepository,
        session=db_session
    )
    
    tenant_service = providers.Factory(
        TenantService,
        tenant_repository=tenant_repository
    )
    
    admit_tenant_use_case = providers.Factory(
        AdmitTenantUseCase,
        tenant_service=tenant_service
    )
```

#### Integration Testing

```python
# Test with real database
@pytest.mark.asyncio
async def test_repository_integration(db_session):
    repository = SQLTenantRepository(db_session)
    
    # Create test data
    tenant = TenantEntity.create_tenant("Integration Test", 1)
    created = await repository.create(tenant)
    
    # Verify
    retrieved = await repository.get_by_id(created.id)
    assert retrieved.name == "Integration Test"
```

### Phase 5: Presentation Layer (Week 5-6)

**Goal:** Create new controllers while keeping old ones

#### Feature Flag Approach

```python
# In main.py
USE_CLEAN_ARCHITECTURE = os.getenv('USE_CLEAN_ARCHITECTURE', 'false').lower() == 'true'

if USE_CLEAN_ARCHITECTURE:
    # New clean controllers
    app.include_router(clean_tenant_router, prefix="/api/v2")
else:
    # Legacy controllers
    app.include_router(legacy_tenant_router, prefix="/api/v1")
```

#### Parallel Controllers

```python
# Keep both working
app.include_router(legacy_tenant_router, prefix="/api/v1")
app.include_router(clean_tenant_router, prefix="/api/v2")
```

## 🧪 Testing Strategy

### Unit Testing Throughout

```bash
# Test each layer independently
pytest tests/domain/ -v          # Domain layer
pytest tests/application/ -v     # Application layer
pytest tests/infrastructure/ -v  # Infrastructure layer
pytest tests/presentation/ -v    # Presentation layer
```

### Integration Testing

```bash
# Test layer interactions
pytest tests/integration/ -v
```

### End-to-End Testing

```bash
# Test complete workflows
pytest tests/e2e/ -v
```

### API Testing

```python
# Test both old and new APIs
def test_legacy_api_still_works():
    response = client.post("/api/v1/tenants", json={"name": "Test"})
    assert response.status_code == 200

def test_new_api_works():
    response = client.post("/api/v2/tenants", 
                          json={"name": "Test", "organization_id": 1})
    assert response.status_code == 200
```

## 📊 Progress Tracking

### Metrics to Track

- **Test Coverage**: Aim for 80%+ coverage
- **API Response Time**: Should not degrade
- **Error Rate**: Monitor for regressions
- **Code Churn**: Track lines of code changed

### Weekly Checkpoints

- **Week 1**: Foundation complete, no functional changes
- **Week 2**: Domain layer working, business logic extracted
- **Week 3**: Use cases and DTOs implemented
- **Week 4**: Dependency injection working
- **Week 5**: New controllers working alongside old ones
- **Week 6**: Migration complete, legacy code removed

## 🚨 Risk Mitigation

### Rollback Strategies

1. **Feature Flags**: Can disable new functionality instantly
2. **Database Rollback**: Schema migrations are reversible
3. **Code Rollback**: Git allows reverting to previous commits
4. **API Versioning**: Old API versions remain available

### Monitoring

```python
# Add health checks
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "legacy_api": "available",
        "clean_api": "available"
    }
```

### Alerting

- Set up alerts for API response time degradation
- Monitor error rates for both old and new endpoints
- Track test suite pass/fail rates

## 🐛 Troubleshooting Common Issues

### Issue: Import Errors

ModuleNotFoundError: No module named 'domain'

**Solution:** Add project root to Python path in all entry points.

### Issue: Database Connection Issues

- Verify DATABASE_URL environment variable
- Check database server is running
- Ensure proper permissions

### Issue: Dependency Injection Problems

```python
# Check container wiring
container = Container()
container.wire(modules=[__name__])
```

### Issue: Test Failures

- Ensure all dependencies are properly mocked
- Check that domain entities match test expectations
- Verify async/await usage is consistent

## 📈 Success Metrics

### Technical Metrics

- ✅ **Test Coverage**: 80%+ across all layers
- ✅ **API Performance**: No degradation in response times
- ✅ **Error Rate**: No increase in error rates
- ✅ **Code Quality**: Clean Architecture patterns followed

### Business Metrics

- ✅ **Zero Downtime**: No service interruptions
- ✅ **Backward Compatibility**: All existing clients work
- ✅ **Developer Productivity**: Faster feature development
- ✅ **Maintainability**: Easier to modify and extend code

## 🎯 Final Migration Steps

### Week 7-8: Production Deployment

1. **Deploy with feature flags disabled**
2. **Enable new functionality gradually**
3. **Monitor performance and errors**
4. **Gather feedback from team**

### Week 9-10: Legacy Removal

1. **Confirm new system is stable**
2. **Update client applications**
3. **Remove legacy code**
4. **Update documentation**

### Week 11-12: Optimization

1. **Performance tuning**
2. **Code cleanup**
3. **Documentation updates**
4. **Team training**

## 📚 Resources

- [Architecture Overview](../01-architecture-overview.md)
- [Quick Start Guide](../02-quick-start.md)
- [Phase Guides](../phases/)
- [Testing Patterns](../patterns/testing.md)
- [Troubleshooting](../troubleshooting.md)

This gradual migration strategy ensures a smooth transition to Clean Architecture while maintaining system stability and team productivity.
