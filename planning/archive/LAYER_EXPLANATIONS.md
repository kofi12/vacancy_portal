# Clean Architecture Layers: Detailed Explanation

## Overview

Clean Architecture divides a system into four distinct layers, each with specific responsibilities and clear boundaries. This separation ensures low coupling, high cohesion, and maintainable code.

## 1. Domain Layer (Core Business Logic)

### **Purpose & Responsibility**

The Domain Layer is the **heart of your application** - it contains the core business logic and rules that are independent of any external concerns. This layer represents what your business actually does, regardless of how it's presented or stored.

### **Key Characteristics**

- **Framework Independent**: No dependencies on FastAPI, SQLModel, or any external libraries
- **Database Agnostic**: Doesn't know or care about databases, file systems, or APIs
- **Business Focused**: Contains the rules that make your business unique
- **Testable**: Easy to unit test without external dependencies

### **Components**

#### **Entities**

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
        """Business rule: tenant is active if not discharged"""
        return self.discharge_date is None
    
    def admit(self, admission_date: datetime) -> None:
        """Business rule: can't admit already admitted tenant"""
        if self.admission_date:
            raise ValueError("Tenant is already admitted")
        self.admission_date = admission_date
        self.waitlist = False
```

**Responsibilities:**

- Represent core business objects with identity and lifecycle
- Contain business logic that belongs to the entity itself
- Enforce business rules and invariants
- Provide rich behavior, not just data

#### **Value Objects**

```python
# domain/value_objects/email.py
@dataclass(frozen=True)
class Email:
    value: str
    
    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise ValueError("Invalid email format")
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        # Email validation logic
        return "@" in email and "." in email.split("@")[1]
```

**Responsibilities:**

- Represent immutable concepts that don't have identity
- Encapsulate validation logic
- Provide type safety and domain meaning
- Prevent primitive obsession

#### **Repository Interfaces**

```python
# domain/repositories/tenant_repository.py
class TenantRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[Tenant]:
        pass
    
    @abstractmethod
    async def get_waitlist_tenants(self) -> List[Tenant]:
        pass
```

**Responsibilities:**

- Define contracts for data access without implementation details
- Enable dependency inversion (domain depends on abstractions)
- Allow for different storage implementations
- Support testing through mocking

#### **Domain Services**

```python
# domain/services/tenant_service.py
class TenantService:
    def __init__(self, tenant_repository: TenantRepository):
        self._tenant_repository = tenant_repository
    
    async def create_tenant(self, tenant: Tenant) -> Tenant:
        # Business rule: check for duplicate names
        existing = await self._tenant_repository.get_by_name(tenant.name)
        if existing:
            raise TenantAlreadyExistsError(f"Tenant {tenant.name} already exists")
        return await self._tenant_repository.create(tenant)
```

**Responsibilities:**

- Handle business logic that doesn't belong to a single entity
- Coordinate between multiple entities
- Enforce complex business rules
- Orchestrate domain operations

#### **Domain Exceptions**

```python
# domain/exceptions/__init__.py
class TenantNotFoundError(DomainException):
    """Raised when tenant is not found"""
    pass

class TenantAlreadyExistsError(DomainException):
    """Raised when tenant already exists"""
    pass
```

**Responsibilities:**

- Represent business-specific error conditions
- Provide meaningful error messages
- Enable proper error handling in upper layers
- Distinguish between technical and business errors

### **Why This Layer Matters**

- **Business Continuity**: Your business rules survive technology changes
- **Testability**: Easy to test business logic in isolation
- **Independence**: Can change databases, frameworks, or UI without affecting business logic
- **Clarity**: Clear separation between what your business does vs. how it's implemented

---

## 2. Application Layer (Use Cases & Orchestration)

### **Purpose & Responsibility**

The Application Layer **orchestrates the flow of data** and coordinates domain objects to perform specific business use cases. It's the bridge between the domain and external concerns, implementing application-specific business rules.

### **Key Characteristics**

- **Use Case Driven**: Each class represents a specific business use case
- **Stateless**: Doesn't maintain state between requests
- **Thin**: Contains minimal logic, mostly coordination
- **Framework Aware**: Knows about HTTP, but not database details

### **Components**

#### **Use Cases**

```python
# application/use_cases/create_tenant_use_case.py
class CreateTenantUseCase:
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
    
    async def execute(self, request: CreateTenantRequest) -> TenantResponse:
        # 1. Validate input
        # 2. Create domain entity
        tenant = Tenant(
            name=request.name,
            organization_id=request.organization_id,
            waitlist=request.waitlist
        )
        
        # 3. Execute business logic
        created_tenant = await self._tenant_service.create_tenant(tenant)
        
        # 4. Return response
        return TenantResponse.from_entity(created_tenant)
```

**Responsibilities:**

- Implement specific business use cases
- Coordinate between domain services
- Handle input validation and transformation
- Manage transaction boundaries
- Return appropriate responses

#### **DTOs (Data Transfer Objects)**

```python
# application/dto/tenant_dto.py
@dataclass
class CreateTenantRequest:
    name: str
    organization_id: int
    waitlist: bool = False

@dataclass
class TenantResponse:
    id: int
    name: str
    is_active: bool
    created_at: datetime
    
    @classmethod
    def from_entity(cls, tenant: Tenant) -> 'TenantResponse':
        return cls(
            id=tenant.id,
            name=tenant.name,
            is_active=tenant.is_active(),
            created_at=tenant.created_at
        )
```

**Responsibilities:**

- Define data structures for input/output
- Separate domain entities from external representations
- Handle data transformation and validation
- Provide type safety for API contracts

#### **Application Services**

```python
# application/services/tenant_application_service.py
class TenantApplicationService:
    def __init__(self, tenant_service: TenantService, notification_service: NotificationService):
        self._tenant_service = tenant_service
        self._notification_service = notification_service
    
    async def create_tenant_with_notification(self, request: CreateTenantRequest) -> TenantResponse:
        # Application-specific workflow
        tenant = await self._tenant_service.create_tenant(request.to_entity())
        await self._notification_service.notify_organization_admin(tenant)
        return TenantResponse.from_entity(tenant)
```

**Responsibilities:**

- Coordinate complex workflows involving multiple use cases
- Handle cross-cutting concerns (logging, notifications)
- Manage application-level business rules
- Orchestrate external service interactions

#### **Interfaces**

```python
# application/interfaces/notification_service.py
class NotificationService(ABC):
    @abstractmethod
    async def notify_organization_admin(self, tenant: Tenant) -> None:
        pass
```

**Responsibilities:**

- Define contracts for external services
- Enable dependency inversion for external concerns
- Support testing through mocking
- Allow for different implementations (email, SMS, push notifications)

### **Why This Layer Matters**

- **Use Case Clarity**: Each class represents a specific business operation
- **API Design**: DTOs define clear contracts for external consumers
- **Workflow Management**: Coordinates complex business processes
- **Testability**: Easy to test business workflows in isolation

---

## 3. Infrastructure Layer (External Concerns)

### **Purpose & Responsibility**

The Infrastructure Layer **implements interfaces** defined by the domain and application layers. It handles all external concerns like databases, APIs, file systems, and frameworks.

### **Key Characteristics**

- **Implementation Heavy**: Contains concrete implementations of abstractions
- **Framework Dependent**: Knows about specific technologies (PostgreSQL, FastAPI, etc.)
- **External Focused**: Handles communication with external systems
- **Configurable**: Supports different environments and configurations

### **Components**

#### **Repository Implementations**

```python
# infrastructure/database/repositories/sql_tenant_repository.py
class SQLTenantRepository(TenantRepository):
    def __init__(self, session: Session):
        self._session = session
    
    async def get_by_id(self, id: int) -> Optional[Tenant]:
        statement = select(TenantModel).where(TenantModel.id == id)
        result = self._session.exec(statement).first()
        return self._to_entity(result) if result else None
    
    async def create(self, tenant: Tenant) -> Tenant:
        tenant_model = TenantModel(
            name=tenant.name,
            admission_date=tenant.admission_date,
            waitlist=tenant.waitlist
        )
        self._session.add(tenant_model)
        self._session.commit()
        return self._to_entity(tenant_model)
```

**Responsibilities:**

- Implement repository interfaces defined in domain
- Handle database-specific operations
- Manage data mapping between domain entities and database models
- Handle database transactions and error handling

#### **Authentication Services**

```python
# infrastructure/auth/jwt_auth_service.py
class JWTAuthService(AuthService):
    def __init__(self, secret_key: str, algorithm: str):
        self._secret_key = secret_key
        self._algorithm = algorithm
    
    async def create_token(self, user: User) -> str:
        payload = {
            "sub": user.email,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "scopes": self._get_user_scopes(user)
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
```

**Responsibilities:**

- Implement authentication and authorization
- Handle JWT token creation and validation
- Manage user sessions and permissions
- Integrate with external auth providers (OAuth, SSO)

#### **File Storage Services**

```python
# infrastructure/file_storage/s3_storage_service.py
class S3StorageService(FileStorageService):
    def __init__(self, s3_client, bucket_name: str):
        self._s3_client = s3_client
        self._bucket_name = bucket_name
    
    async def upload_file(self, file_data: bytes, file_name: str) -> str:
        response = self._s3_client.put_object(
            Bucket=self._bucket_name,
            Key=file_name,
            Body=file_data
        )
        return f"s3://{self._bucket_name}/{file_name}"
```

**Responsibilities:**

- Handle file uploads and downloads
- Manage file metadata and organization
- Implement storage-specific optimizations
- Handle storage errors and retries

#### **External API Services**

```python
# infrastructure/external/email_service.py
class SendGridEmailService(EmailService):
    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = SendGridAPIClient(api_key)
    
    async def send_email(self, to_email: str, subject: str, content: str) -> None:
        message = Mail(
            from_email='noreply@vacancyportal.ca',
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        self._client.send(message)
```

**Responsibilities:**

- Integrate with external APIs and services
- Handle API-specific authentication and formatting
- Manage rate limiting and error handling
- Provide fallback mechanisms

### **Why This Layer Matters**

- **Technology Flexibility**: Can swap implementations without affecting business logic
- **Environment Support**: Supports different configurations for dev/staging/prod
- **External Integration**: Handles all external system communications
- **Performance Optimization**: Can optimize for specific technologies

---

## 4. Presentation Layer (API & UI)

### **Purpose & Responsibility**

The Presentation Layer **handles user interactions** and external requests. It's responsible for receiving input, validating it, and returning appropriate responses.

### **Key Characteristics**

- **Framework Specific**: Knows about FastAPI, HTTP, and web concepts
- **Input/Output Focused**: Handles request/response formatting
- **Stateless**: Each request is independent
- **Validation Heavy**: Ensures data integrity before processing

### **Components**

#### **Controllers**

```python
# presentation/controllers/tenant_controller.py
@tenant_router.post('/create-tenant', response_model=TenantResponse)
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(),
    current_user = Security(get_current_user_with_scopes, scopes=["write:tenants"])
):
    try:
        return await use_case.execute(request)
    except TenantAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Responsibilities:**

- Handle HTTP requests and responses
- Validate input data
- Authenticate and authorize users
- Transform domain exceptions to HTTP responses
- Manage request/response formatting

#### **Middleware**

```python
# presentation/middleware/auth_middleware.py
class AuthMiddleware:
    def __init__(self, auth_service: AuthService):
        self._auth_service = auth_service
    
    async def __call__(self, request: Request, call_next):
        # Extract token from request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Missing token")
        
        # Validate token
        user = await self._auth_service.validate_token(token)
        request.state.user = user
        
        return await call_next(request)
```

**Responsibilities:**

- Handle cross-cutting concerns (authentication, logging, CORS)
- Process requests before they reach controllers
- Add context to requests (user, session, etc.)
- Handle common error scenarios

#### **Serializers**

```python
# presentation/serializers/tenant_serializer.py
class TenantSerializer:
    @staticmethod
    def to_response(tenant: Tenant) -> dict:
        return {
            "id": tenant.id,
            "name": tenant.name,
            "status": "active" if tenant.is_active() else "discharged",
            "created_at": tenant.created_at.isoformat()
        }
    
    @staticmethod
    def from_request(data: dict) -> CreateTenantRequest:
        return CreateTenantRequest(
            name=data["name"],
            organization_id=data["organization_id"],
            waitlist=data.get("waitlist", False)
        )
```

**Responsibilities:**

- Transform data between external and internal formats
- Handle data validation and sanitization
- Manage API versioning and backward compatibility
- Provide consistent response formats

#### **Validators**

```python
# presentation/validators/tenant_validator.py
class TenantValidator:
    @staticmethod
    def validate_create_request(data: dict) -> List[str]:
        errors = []
        
        if not data.get("name"):
            errors.append("Name is required")
        
        if len(data.get("name", "")) > 100:
            errors.append("Name must be less than 100 characters")
        
        if not data.get("organization_id"):
            errors.append("Organization ID is required")
        
        return errors
```

**Responsibilities:**

- Validate input data before processing
- Ensure data integrity and security
- Provide meaningful error messages
- Support different validation rules for different contexts

### **Why This Layer Matters**

- **User Experience**: Handles how users interact with your system
- **API Design**: Defines clear contracts for external consumers
- **Security**: Validates and sanitizes all input
- **Flexibility**: Can support multiple presentation formats (REST API, GraphQL, WebSocket)

---

## Layer Interactions & Dependencies

### **Dependency Flow**

```mermaid
Presentation Layer
       ↓ (depends on)
Application Layer
       ↓ (depends on)
Domain Layer
       ↑ (implements)
Infrastructure Layer
```

### **Key Rules**

1. **Dependencies Point Inward**: Outer layers depend on inner layers
2. **Domain Independence**: Domain layer has no dependencies on outer layers
3. **Interface Contracts**: Outer layers depend on interfaces, not implementations
4. **Data Flow**: Data flows from outer layers inward, responses flow outward

### **Example Flow**

1. **HTTP Request** → Presentation Layer (Controller)
2. **Controller** → Application Layer (Use Case)
3. **Use Case** → Domain Layer (Service)
4. **Service** → Infrastructure Layer (Repository)
5. **Repository** → Database
6. **Response flows back** through all layers

### **Benefits of This Structure**

- **Testability**: Each layer can be tested independently
- **Maintainability**: Changes are isolated to specific layers
- **Flexibility**: Can change implementations without affecting other layers
- **Scalability**: Can scale layers independently
- **Team Development**: Different teams can work on different layers

This layered architecture ensures that your business logic remains pure and independent, while external concerns are properly isolated and manageable.
