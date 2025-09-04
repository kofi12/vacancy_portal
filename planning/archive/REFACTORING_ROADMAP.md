# Refactoring Roadmap: From Current to Clean Architecture

## Current State Analysis

### Issues Identified

1. **High Coupling**: Controllers directly depend on DAO implementations
2. **Low Cohesion**: Business logic mixed with HTTP concerns
3. **No Dependency Inversion**: Direct imports of concrete classes
4. **Inconsistent Error Handling**: Mixed exception strategies
5. **Tight Framework Coupling**: FastAPI concerns throughout the codebase

## Phase 1: Foundation Setup (Week 1)

### 1.1 Create New Directory Structure

```bash
mkdir -p domain/{entities,repositories,services,exceptions,value_objects}
mkdir -p application/{use_cases,dto,interfaces,services}
mkdir -p infrastructure/{database,auth,file_storage,external}
mkdir -p presentation/{controllers,middleware,serializers,validators}
```

### 1.2 Add Dependencies

```toml
# pyproject.toml additions
[tool.poetry.dependencies]
dependency-injector = "^4.41.0"
pydantic = "^2.7.4"  # Already present
```

### 1.3 Create Base Classes

- Implement `BaseEntity` abstract class
- Create `BaseRepository` interface
- Define `DomainException` hierarchy

## Phase 2: Domain Layer Implementation (Week 2)

### 2.1 Tenant Entity Refactoring

**Priority: HIGH** (Start with most complex entity)

**Current Issues:**

- Business logic in DAO layer
- No domain validation
- Mixed concerns

**Actions:**

1. Create `domain/entities/tenant.py`
2. Move business logic from DAO to domain service
3. Add domain validation rules
4. Create `TenantRepository` interface

**Files to Create:**

- `domain/entities/tenant.py`
- `domain/repositories/tenant_repository.py`
- `domain/services/tenant_service.py`
- `domain/exceptions/tenant_exceptions.py`

### 2.2 User Entity Refactoring

**Priority: HIGH** (Core authentication entity)

**Actions:**

1. Create `domain/entities/user.py`
2. Implement user domain logic
3. Create `UserRepository` interface
4. Add user validation rules

### 2.3 Organization Entity Refactoring

#### Priority: MEDIUM

**Actions:**

1. Create `domain/entities/organization.py`
2. Implement organization domain logic
3. Create `OrganizationRepository` interface

## Phase 3: Application Layer Implementation (Week 3)

### 3.1 Use Cases Implementation

#### Priority: HIGH

**Tenant Use Cases:**

- `CreateTenantUseCase`
- `GetTenantUseCase`
- `UpdateTenantUseCase`
- `DeleteTenantUseCase`
- `GetWaitlistTenantsUseCase`

**User Use Cases:**

- `CreateUserUseCase`
- `GetUserUseCase`
- `UpdateUserUseCase`
- `AuthenticateUserUseCase`

### 3.2 DTOs Implementation

#### Priority: HIGH

**Create DTOs for:**

- Tenant operations (Create, Update, Response)
- User operations (Create, Update, Response)
- Organization operations (Create, Update, Response)

## Phase 4: Infrastructure Layer Implementation (Week 4)

### 4.1 Repository Implementations

#### Priority: HIGH

**Actions:**

1. Implement `SQLTenantRepository`
2. Implement `SQLUserRepository`
3. Implement `SQLOrganizationRepository`
4. Add proper error handling
5. Implement transaction management

### 4.2 Dependency Injection Setup

#### Priority: HIGH

**Actions:**

1. Create `infrastructure/container.py`
2. Configure dependency injection
3. Wire up all dependencies
4. Test dependency resolution

### 4.3 Authentication Refactoring

#### Priority: HIGH

**Current Issues:**

- Authentication logic scattered
- Direct database dependencies
- Mixed concerns

**Actions:**

1. Create `infrastructure/auth/jwt_service.py`
2. Create `infrastructure/auth/oauth_service.py`
3. Implement `AuthRepository` interface
4. Move authentication logic to infrastructure

## Phase 5: Presentation Layer Implementation (Week 5)

### 5.1 Controller Refactoring

#### Priority: HIGH

**Actions:**

1. Refactor `tenant_controller.py`
2. Refactor `user_controller.py`
3. Refactor `organization_controller.py`
4. Add proper error handling
5. Implement request/response serialization

### 5.2 Middleware Implementation

#### Priority: MEDIUM

**Actions:**

1. Create authentication middleware
2. Implement logging middleware
3. Add error handling middleware
4. Create CORS middleware

## Phase 6: Migration and Testing (Week 6)

### 6.1 Gradual Migration Strategy

#### Priority: HIGH

**Step-by-Step Approach:**

1. **Week 1-2**: Implement new structure alongside old
2. **Week 3-4**: Create new endpoints with new architecture
3. **Week 5**: Migrate existing endpoints one by one
4. **Week 6**: Remove old code and clean up

### 6.2 Testing Strategy

#### Priority: HIGH

**Actions:**

1. Create unit tests for domain services
2. Create integration tests for use cases
3. Create repository tests
4. Create controller tests
5. Implement end-to-end tests

## Specific Implementation Tasks

### Task 1: Create Domain Entities (Day 1-2)

```python
# domain/entities/tenant.py
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
    
    def admit(self, admission_date: datetime) -> None:
        self.admission_date = admission_date
        self.waitlist = False
    
    def discharge(self, discharge_date: datetime) -> None:
        self.discharge_date = discharge_date
```

### Task 2: Implement Repository Interface (Day 3)

```python
# domain/repositories/tenant_repository.py
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
```

### Task 3: Create Domain Service (Day 4)

```python
# domain/services/tenant_service.py
class TenantService:
    def __init__(self, tenant_repository: TenantRepository):
        self._tenant_repository = tenant_repository
    
    async def create_tenant(self, tenant: Tenant) -> Tenant:
        existing_tenant = await self._tenant_repository.get_by_name(tenant.name)
        if existing_tenant:
            raise TenantAlreadyExistsError(f"Tenant {tenant.name} already exists")
        
        return await self._tenant_repository.create(tenant)
```

### Task 4: Implement Use Cases (Day 5-6)

```python
# application/use_cases/tenant_use_cases.py
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
```

## Risk Mitigation

### 1. **Backward Compatibility**

- Keep old endpoints during migration
- Use feature flags for gradual rollout
- Maintain database schema compatibility

### 2. **Testing Strategy**

- Comprehensive unit tests before migration
- Integration tests for critical paths
- End-to-end tests for user workflows

### 3. **Rollback Plan**

- Keep old code until new code is proven stable
- Database migrations are reversible
- Feature flags for quick rollback

## Success Metrics

### 1. **Code Quality**

- Reduce cyclomatic complexity by 50%
- Increase test coverage to 80%+
- Eliminate circular dependencies

### 2. **Maintainability**

- Reduce time to add new features by 40%
- Decrease bug rate by 30%
- Improve code review efficiency

### 3. **Performance**

- Maintain or improve response times
- Reduce memory usage
- Improve database query efficiency

## Timeline Summary

| Week | Focus | Deliverables |
|------|-------|--------------|
| 1 | Foundation | Directory structure, base classes, dependencies |
| 2 | Domain Layer | Entities, repositories, domain services |
| 3 | Application Layer | Use cases, DTOs, application services |
| 4 | Infrastructure | Repository implementations, DI container |
| 5 | Presentation | Controllers, middleware, serializers |
| 6 | Migration | Testing, gradual migration, cleanup |

## Next Steps

1. **Immediate Actions** (This Week):
   - Set up new directory structure
   - Add dependency-injector to pyproject.toml
   - Create base classes and interfaces

2. **Week 1 Goals**:
   - Complete domain layer for Tenant entity
   - Implement basic repository interface
   - Create domain service with business logic

3. **Success Criteria**:
   - New Tenant domain entity working
   - Repository interface defined
   - Basic use case implemented
   - Unit tests passing

This roadmap provides a clear path from your current architecture to a clean, maintainable, and extensible system following SOLID principles and dependency inversion.
