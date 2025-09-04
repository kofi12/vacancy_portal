# 📚 Architecture Overview: Clean Architecture for Vacancy Portal

## 🎯 Purpose

This document provides a **high-level understanding** of Clean Architecture and how we're applying it to transform the Vacancy Portal from tightly-coupled code to a maintainable, scalable system.

## 🏛️ What is Clean Architecture?

Clean Architecture is a software design philosophy that **separates concerns** and **inverts dependencies** to create systems that are:

- **Independent of frameworks** - Can change web frameworks without affecting business logic
- **Testable** - Each component can be tested in isolation  
- **Independent of UI** - Business logic doesn't depend on how it's presented
- **Independent of database** - Can swap databases without changing business rules
- **Independent of external agencies** - Business logic doesn't depend on external services

## 🏗️ The Four Layers

### 1. 🎯 Domain Layer (Core Business Logic)

**What it contains:**

- **Entities**: Core business objects (Tenant, Organization, User)
- **Value Objects**: Immutable concepts (Email, Address)
- **Repository Interfaces**: Contracts for data access
- **Domain Services**: Business logic that spans multiple entities
- **Domain Exceptions**: Business-specific error types

**Key Principle:** This layer has **zero dependencies** on external frameworks or technologies.

```python
# Domain Entity Example
@dataclass
class TenantEntity(BaseEntity):
    name: str
    admission_date: Optional[datetime] = None
    is_waitlist: bool = False
    
    def can_be_admitted(self) -> bool:
        """Business rule: tenant admission logic"""
        return self.is_waitlist and self.admission_date is None
```

### 2. ⚙️ Application Layer (Use Cases & Orchestration)

**What it contains:**

- **Use Cases**: Specific business operations (CreateTenant, AdmitTenant)
- **DTOs**: Data structures for input/output
- **Application Services**: Orchestration between domain objects
- **Input Validation**: Request validation logic

**Key Principle:** Orchestrates domain objects to perform business operations.

```python
# Use Case Example
class AdmitTenantUseCase:
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self, request: AdmitTenantRequest) -> TenantResponse:
        # 1. Validate input
        # 2. Execute business logic
        tenant = await self._tenant_service.admit_tenant(
            request.tenant_id, request.admission_date
        )
        # 3. Return response
        return TenantResponse.from_entity(tenant)
```

### 3. 🔧 Infrastructure Layer (External Concerns)

**What it contains:**

- **Repository Implementations**: Database access (SQLTenantRepository)
- **Authentication Services**: OAuth, JWT implementations
- **External APIs**: Third-party service integrations
- **File Storage**: S3, local file system implementations

**Key Principle:** Implements interfaces defined by domain and application layers.

```python
# Repository Implementation Example
class SQLTenantRepository(TenantRepository):
    def __init__(self, session: Session):
        self._session = session
    
    async def get_by_id(self, id: int) -> Optional[TenantEntity]:
        statement = select(TenantModel).where(TenantModel.id == id)
        result = self._session.exec(statement).first()
        return self._to_entity(result) if result else None
```

### 4. 🌐 Presentation Layer (API Controllers)

**What it contains:**

- **HTTP Controllers**: FastAPI route handlers
- **Middleware**: Cross-cutting concerns (logging, authentication)
- **Request/Response Models**: API serialization
- **Input Validation**: Request validation

**Key Principle:** Handles HTTP requests and formats responses.

```python
# Controller Example
@tenant_router.post('/admit-tenant')
async def admit_tenant(
    request: AdmitTenantRequest,
    use_case: AdmitTenantUseCase = Depends(get_admit_tenant_use_case)
):
    return await use_case.execute(request)
```

## 🔄 Dependency Flow

``` mermaid
Presentation Layer
       ↓ (depends on)
Application Layer
       ↓ (depends on)
Domain Layer
       ↑ (implements)
Infrastructure Layer
```

**Key Rules:**

1. **Outer layers depend on inner layers**
2. **Inner layers don't depend on outer layers**
3. **Dependencies point inward toward the domain**
4. **Infrastructure implements domain interfaces**

## 🎨 Design Patterns Used

### Repository Pattern

```python
# Domain Interface (Abstraction)
class TenantRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[Tenant]:
        pass

# Infrastructure Implementation (Concrete)
class SQLTenantRepository(TenantRepository):
    async def get_by_id(self, id: int) -> Optional[Tenant]:
        # SQL implementation
        pass
```

### Use Case Pattern

```python
# Application Layer
class CreateTenantUseCase:
    def __init__(self, tenant_repository: TenantRepository):
        self._repository = tenant_repository
    
    async def execute(self, request) -> Response:
        # Orchestrate domain objects
        tenant = Tenant(request.name, request.organization_id)
        return await self._repository.create(tenant)
```

### Dependency Injection

```python
# Wiring dependencies
def get_create_tenant_use_case() -> CreateTenantUseCase:
    repository = SQLTenantRepository(session=get_db_session())
    return CreateTenantUseCase(repository)
```

## 🚀 Benefits You'll See

### For Individual Developers

- **Easier Testing**: Test business logic without database or web framework
- **Faster Development**: Clear patterns for common operations
- **Better Code Organization**: Know exactly where to put new code
- **Framework Independence**: Can change technologies without affecting business logic

### For the Team

- **Consistent Code**: Everyone follows the same patterns
- **Easier Onboarding**: New developers understand the structure quickly
- **Parallel Development**: Teams can work on different layers simultaneously
- **Reduced Bugs**: Clear separation reduces unexpected side effects

### For the Business

- **Faster Feature Delivery**: Less coupling means faster development
- **Easier Maintenance**: Changes are localized to specific layers
- **Technology Flexibility**: Can swap databases, frameworks, or services
- **Scalability**: Each layer can be scaled independently

## 📊 Before vs After Comparison

### Current Architecture Issues

❌ Controllers directly call DAOs
❌ Business logic scattered across files
❌ Hard to test individual components
❌ Tight coupling to FastAPI/SQLModel
❌ Difficult to add new features

### Clean Architecture Benefits

✅ Domain layer independent of frameworks
✅ Business logic centralized and testable
✅ Each layer has single responsibility
✅ Easy to swap technologies
✅ Simple to add new features

## 🧪 Testing Strategy

### Unit Tests (Domain Layer)

```python
def test_tenant_can_be_admitted():
    tenant = TenantEntity.create_tenant("John", 1, is_waitlist=True)
    assert tenant.can_be_admitted() == True
```

### Integration Tests (Layer Interactions)

```python
def test_create_tenant_workflow():
    # Test complete workflow from controller to database
    pass
```

### End-to-End Tests (Full System)

```python
def test_tenant_admission_api():
    # Test complete API workflow
    pass
```

## 🔄 Migration Strategy

### Phase Approach

1. **Domain Layer First**: Business logic and rules
2. **Application Layer**: Use cases and orchestration  
3. **Infrastructure Layer**: Repository implementations
4. **Presentation Layer**: Controller refactoring

### Zero Breaking Changes

- Keep existing API working during migration
- Use feature flags for gradual rollout
- Maintain backward compatibility
- Rollback capability if needed

## 🎯 Success Criteria

After implementation, you'll have:

- ✅ **80%+ test coverage**
- ✅ **Zero breaking changes** to existing API
- ✅ **Business logic independent** of frameworks
- ✅ **Easy to add new features**
- ✅ **Simple to change technologies**

## 🆘 Common Questions

**Q: Why not just use the current structure?**
A: The current structure works for small projects but becomes unmaintainable as the codebase grows. Clean Architecture provides a scalable foundation.

**Q: Is this overkill for our project?**
A: For a system handling tenant admissions and organization management, Clean Architecture provides the right level of structure without being overly complex.

**Q: How long will this take?**
A: 4-6 weeks for complete migration, but you'll see benefits from day one as you start implementing the domain layer.

**Q: What if something goes wrong?**
A: Each phase is designed to be reversible, and we maintain the existing API throughout the migration.

## 📚 Next Steps

Now that you understand the architecture:

1. **[Follow the Quick Start](02-quick-start.md)** to implement your first domain entity
2. **Explore the [Patterns](patterns/)** folder for detailed implementation examples
3. **Check the [Phase Guides](phases/)** for step-by-step implementation

---

**Ready to start implementing?** → [Quick Start Guide](02-quick-start.md)

## What This Document Provides

This Architecture Overview gives new developers:

1. **High-level understanding** of Clean Architecture concepts
2. **Concrete examples** from your codebase
3. **Clear benefits** they'll see from the refactoring
4. **Visual diagrams** showing the layer relationships
5. **Testing strategy** explanation
6. **Migration approach** overview
7. **Success criteria** to measure progress

The document is designed to be:

- ✅ **Accessible** to developers at all levels
- ✅ **Practical** with real code examples
- ✅ **Motivational** showing clear benefits
- ✅ **Actionable** with next steps
