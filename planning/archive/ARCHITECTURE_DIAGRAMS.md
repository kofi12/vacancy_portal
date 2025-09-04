# Architecture Diagrams for Vacancy Portal

## Overview

This document contains diagrams at various levels of abstraction to help conceptualize the Clean Architecture implementation for the Vacancy Portal.

## 1. High-Level Architecture Overview

### Current vs. Target Architecture

```mermaid
graph TB
    subgraph "Current Architecture"
        A1[Controllers] --> B1[DAOs]
        B1 --> C1[Database]
        A1 --> D1[Business Logic]
        D1 --> B1
    end
    
    subgraph "Target Clean Architecture"
        A2[Presentation Layer] --> B2[Application Layer]
        B2 --> C2[Domain Layer]
        D2[Infrastructure Layer] --> C2
        A2 -.-> D2
    end
    
    style A1 fill:#ffcccc
    style B1 fill:#ffcccc
    style D1 fill:#ffcccc
    style A2 fill:#ccffcc
    style B2 fill:#ccffcc
    style C2 fill:#ccffcc
    style D2 fill:#ccffcc
```

### Dependency Flow

```mermaid
graph TD
    A[Presentation Layer<br/>Controllers, Middleware] --> B[Application Layer<br/>Use Cases, DTOs]
    B --> C[Domain Layer<br/>Entities, Services]
    D[Infrastructure Layer<br/>Repositories, External Services] --> C
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
```

## 2. Layer Details

### Domain Layer Structure

```mermaid
graph TD
    subgraph "Domain Layer"
        A[Entities<br/>Tenant, User, Organization] --> B[Value Objects<br/>Email, Address, DateRange]
        A --> C[Repository Interfaces<br/>TenantRepository, UserRepository]
        A --> D[Domain Services<br/>TenantService, UserService]
        A --> E[Domain Exceptions<br/>TenantNotFoundError, ValidationError]
    end
    
    style A fill:#e8f5e8
    style B fill:#e8f5e8
    style C fill:#e8f5e8
    style D fill:#e8f5e8
    style E fill:#e8f5e8
```

### Application Layer Structure

```mermaid
graph TD
    subgraph "Application Layer"
        A[Use Cases<br/>CreateTenant, GetTenant, UpdateTenant] --> B[DTOs<br/>CreateTenantRequest, TenantResponse]
        A --> C[Application Services<br/>TenantApplicationService]
        A --> D[Interfaces<br/>NotificationService, EmailService]
    end
    
    style A fill:#f3e5f5
    style B fill:#f3e5f5
    style C fill:#f3e5f5
    style D fill:#f3e5f5
```

### Infrastructure Layer Structure

```mermaid
graph TD
    subgraph "Infrastructure Layer"
        A[Database<br/>SQLTenantRepository, SQLUserRepository] --> B[Authentication<br/>JWTAuthService, OAuthService]
        A --> C[File Storage<br/>S3StorageService, LocalStorageService]
        A --> D[External APIs<br/>EmailService, NotificationService]
    end
    
    style A fill:#fff3e0
    style B fill:#fff3e0
    style C fill:#fff3e0
    style D fill:#fff3e0
```

### Presentation Layer Structure

```mermaid
graph TD
    subgraph "Presentation Layer"
        A[Controllers<br/>TenantController, UserController] --> B[Middleware<br/>AuthMiddleware, LoggingMiddleware]
        A --> C[Serializers<br/>TenantSerializer, UserSerializer]
        A --> D[Validators<br/>TenantValidator, UserValidator]
    end
    
    style A fill:#e1f5fe
    style B fill:#e1f5fe
    style C fill:#e1f5fe
    style D fill:#e1f5fe
```

## 3. Detailed Component Interactions

### Tenant Management Flow

```mermaid
sequenceDiagram
    participant Client
    participant TenantController
    participant CreateTenantUseCase
    participant TenantService
    participant TenantRepository
    participant Database
    
    Client->>TenantController: POST /api/tenants/create-tenant
    TenantController->>CreateTenantUseCase: execute(request)
    CreateTenantUseCase->>TenantService: create_tenant(tenant)
    TenantService->>TenantRepository: get_by_name(name)
    TenantRepository->>Database: SELECT * FROM tenants WHERE name = ?
    Database-->>TenantRepository: null (not found)
    TenantService->>TenantRepository: create(tenant)
    TenantRepository->>Database: INSERT INTO tenants (...)
    Database-->>TenantRepository: tenant with ID
    TenantRepository-->>TenantService: tenant entity
    TenantService-->>CreateTenantUseCase: tenant entity
    CreateTenantUseCase-->>TenantController: TenantResponse
    TenantController-->>Client: 201 Created + tenant data
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant AuthController
    participant AuthService
    participant UserRepository
    participant JWTService
    participant Database
    
    Client->>AuthController: POST /api/auth/login
    AuthController->>AuthService: authenticate(email, password)
    AuthService->>UserRepository: get_by_email(email)
    UserRepository->>Database: SELECT * FROM users WHERE email = ?
    Database-->>UserRepository: user data
    UserRepository-->>AuthService: user entity
    AuthService->>JWTService: create_token(user)
    JWTService-->>AuthService: JWT token
    AuthService-->>AuthController: auth result
    AuthController-->>Client: 200 OK + JWT token
```

## 4. Database Schema Evolution

### Current Schema

```mermaid
erDiagram
    USERS {
        int id PK
        string email UK
        string first_name
        string last_name
        string community_org
        string role
    }
    
    ORGANIZATIONS {
        int id PK
        string business_name
        string address
        int number_of_beds
        int owner_id FK
    }
    
    TENANTS {
        int id PK
        string name
        datetime admission_date
        datetime discharge_date
        boolean waitlist
        int organization_id FK
    }
    
    DOCUMENTS {
        int id PK
        string file_name
        string url
        int tenant_id FK
    }
    
    USERS ||--o{ ORGANIZATIONS : owns
    ORGANIZATIONS ||--o{ TENANTS : manages
    TENANTS ||--o{ DOCUMENTS : has
```

### Enhanced Schema (Future)

```mermaid
erDiagram
    USERS {
        int id PK
        string email UK
        string first_name
        string last_name
        string community_org
        string role
        datetime created_at
        datetime updated_at
    }
    
    ORGANIZATIONS {
        int id PK
        string business_name
        string address
        int number_of_beds
        int owner_id FK
        datetime created_at
        datetime updated_at
    }
    
    TENANTS {
        int id PK
        string name
        datetime admission_date
        datetime discharge_date
        boolean waitlist
        int organization_id FK
        datetime created_at
        datetime updated_at
    }
    
    DOCUMENTS {
        int id PK
        string file_name
        string url
        int tenant_id FK
        string document_type
        datetime created_at
        datetime updated_at
    }
    
    AUDIT_LOGS {
        int id PK
        string entity_type
        int entity_id
        string action
        json old_values
        json new_values
        int user_id FK
        datetime created_at
    }
    
    USERS ||--o{ ORGANIZATIONS : owns
    ORGANIZATIONS ||--o{ TENANTS : manages
    TENANTS ||--o{ DOCUMENTS : has
    USERS ||--o{ AUDIT_LOGS : creates
```

## 5. Dependency Injection Container

```mermaid
graph TD
    subgraph "Container Configuration"
        A[Database Session] --> B[Repositories]
        B --> C[Domain Services]
        C --> D[Use Cases]
        D --> E[Controllers]
        
        B1[SQLTenantRepository] --> B
        B2[SQLUserRepository] --> B
        B3[SQLOrganizationRepository] --> B
        
        C1[TenantService] --> C
        C2[UserService] --> C
        C3[OrganizationService] --> C
        
        D1[CreateTenantUseCase] --> D
        D2[GetTenantUseCase] --> D
        D3[UpdateTenantUseCase] --> D
    end
    
    style A fill:#fff3e0
    style B fill:#fff3e0
    style C fill:#e8f5e8
    style D fill:#f3e5f5
    style E fill:#e1f5fe
```

## 6. Migration Strategy Visualization

### Phase-by-Phase Migration

```mermaid
gantt
    title Migration Timeline
    dateFormat  YYYY-MM-DD
    section Foundation
    Directory Structure    :done, setup, 2024-01-01, 2d
    Base Classes          :done, base, 2024-01-03, 3d
    Dependencies          :done, deps, 2024-01-06, 1d
    
    section Domain Layer
    Entities              :active, entities, 2024-01-07, 5d
    Repository Interfaces :repos, 2024-01-12, 3d
    Domain Services       :services, 2024-01-15, 4d
    
    section Application Layer
    DTOs                  :dto, 2024-01-19, 3d
    Use Cases             :usecases, 2024-01-22, 5d
    Application Services  :appservices, 2024-01-27, 3d
    
    section Infrastructure
    Repository Impl       :repoimpl, 2024-01-30, 5d
    DI Container          :container, 2024-02-04, 3d
    Auth Services         :auth, 2024-02-07, 4d
    
    section Presentation
    Controllers           :controllers, 2024-02-11, 5d
    Middleware            :middleware, 2024-02-16, 3d
    Serializers           :serializers, 2024-02-19, 2d
    
    section Testing & Migration
    Unit Tests            :tests, 2024-02-21, 5d
    Integration Tests     :integration, 2024-02-26, 4d
    Gradual Migration     :migration, 2024-03-01, 7d
    Cleanup               :cleanup, 2024-03-08, 3d
```

## 7. Testing Strategy

### Testing Pyramid

```mermaid
graph TD
    subgraph "Testing Strategy"
        A[End-to-End Tests<br/>10%] --> B[Integration Tests<br/>20%]
        B --> C[Unit Tests<br/>70%]
        
        A1[API Tests<br/>User Workflows] --> A
        A2[UI Tests<br/>Critical Paths] --> A
        
        B1[Repository Tests<br/>Database Integration] --> B
        B2[Service Tests<br/>Business Logic] --> B
        
        C1[Entity Tests<br/>Domain Logic] --> C
        C2[Use Case Tests<br/>Application Logic] --> C
        C3[Controller Tests<br/>HTTP Logic] --> C
    end
    
    style A fill:#ffebee
    style B fill:#fff3e0
    style C fill:#e8f5e8
```

## 8. Deployment Architecture

### Current vs. Target Deployment

```mermaid
graph TB
    subgraph "Current Deployment"
        A1[Single App Server] --> B1[PostgreSQL Database]
        A1 --> C1[File System Storage]
    end
    
    subgraph "Target Deployment"
        A2[Load Balancer] --> B2[App Server 1]
        A2 --> C2[App Server 2]
        A2 --> D2[App Server N]
        
        B2 --> E2[PostgreSQL Primary]
        C2 --> E2
        D2 --> E2
        
        E2 --> F2[PostgreSQL Replica]
        
        B2 --> G2[S3 Storage]
        C2 --> G2
        D2 --> G2
        
        H2[Redis Cache] --> B2
        H2 --> C2
        H2 --> D2
    end
    
    style A1 fill:#ffcccc
    style B1 fill:#ffcccc
    style C1 fill:#ffcccc
    style A2 fill:#ccffcc
    style B2 fill:#ccffcc
    style C2 fill:#ccffcc
    style D2 fill:#ccffcc
    style E2 fill:#ccffcc
    style F2 fill:#ccffcc
    style G2 fill:#ccffcc
    style H2 fill:#ccffcc
```

## 9. Error Handling Flow

```mermaid
graph TD
    A[HTTP Request] --> B{Valid Request?}
    B -->|No| C[Validation Error<br/>400 Bad Request]
    B -->|Yes| D[Controller]
    D --> E{Authentication?}
    E -->|No| F[Auth Error<br/>401 Unauthorized]
    E -->|Yes| G{Authorization?}
    G -->|No| H[Permission Error<br/>403 Forbidden]
    G -->|Yes| I[Use Case]
    I --> J{Domain Validation?}
    J -->|No| K[Domain Error<br/>400 Bad Request]
    J -->|Yes| L[Domain Service]
    L --> M{Business Rule?}
    M -->|No| N[Business Error<br/>400 Bad Request]
    M -->|Yes| O[Repository]
    O --> P{Database Error?}
    P -->|Yes| Q[Database Error<br/>500 Internal Server Error]
    P -->|No| R[Success Response<br/>200 OK]
    
    style C fill:#ffebee
    style F fill:#ffebee
    style H fill:#ffebee
    style K fill:#ffebee
    style N fill:#ffebee
    style Q fill:#ffebee
    style R fill:#e8f5e8
```

## 10. Performance Monitoring

### Key Metrics Dashboard

```mermaid
graph LR
    subgraph "Performance Metrics"
        A[Response Time<br/>Avg: 150ms] --> B[Throughput<br/>1000 req/s]
        B --> C[Error Rate<br/>0.1%]
        C --> D[Database Queries<br/>Avg: 2.5/request]
        D --> E[Memory Usage<br/>512MB]
        E --> F[CPU Usage<br/>45%]
        F --> A
    end
    
    style A fill:#e3f2fd
    style B fill:#e8f5e8
    style C fill:#fff3e0
    style D fill:#f3e5f5
    style E fill:#ffebee
    style F fill:#fce4ec
```

## Summary

These diagrams provide multiple perspectives on the Clean Architecture implementation:

1. **High-Level Overview**: Shows the transformation from current to target architecture
2. **Layer Details**: Explains the structure and responsibilities of each layer
3. **Component Interactions**: Demonstrates how components communicate
4. **Database Evolution**: Shows schema improvements over time
5. **Dependency Injection**: Illustrates how dependencies are managed
6. **Migration Strategy**: Provides a timeline for implementation
7. **Testing Strategy**: Shows the testing pyramid approach
8. **Deployment Architecture**: Compares current vs. target deployment
9. **Error Handling**: Demonstrates comprehensive error management
10. **Performance Monitoring**: Shows key metrics to track

These visualizations will help you understand the architecture at different levels and execute the implementation plan effectively.
