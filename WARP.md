# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

The Vacancy Portal is a FastAPI-based web application that bridges the communication gap between Residential Care Facility (RCF) management and social workers. It allows RCFs to manage vacancy data, social workers to view vacancies and manage waitlists, handle document uploads for potential tenants, and schedule viewings.

### 🚧 Current Refactor Status

**The project is currently undergoing a Clean Architecture refactor** to improve maintainability, testability, and scalability. The refactor documentation is located in the `planning/` folder.

**Migration Progress:**
- ✅ Planning phase complete with comprehensive documentation
- 🚧 Currently implementing Domain Layer (Phase 1)
- ⏳ Application Layer (Phase 2) - Next
- ⏳ Infrastructure Layer (Phase 3) - Planned
- ⏳ Presentation Layer (Phase 4) - Planned

**For developers working on this codebase:**
- Read the [Architecture Overview](planning/01-architecture-overview.md) first
- Follow the [Quick Start Guide](planning/02-quick-start.md) for hands-on implementation
- Check the [Phase Guides](planning/phases/) for detailed implementation steps
- Use the [Patterns](planning/patterns/) folder for code examples

## Development Commands

### Environment Setup
```bash
# Install dependencies using Poetry
poetry install

# Activate virtual environment
poetry shell
```

### Running the Application
```bash
# Development environment (with PostgreSQL database)
./run-dev.sh
# Equivalent to: docker compose up --build

# Test environment (separate test database)
./run-test.sh  
# Equivalent to: docker compose -f compose.test.yml up --build

# Direct FastAPI development server (requires local DB setup)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Database Management
```bash
# Generate new Alembic migration in test environment
./generate-migration-test.sh "migration description"

# Apply migrations (handled automatically on app startup if DATABASE_URL is set)
alembic upgrade head

# Create new migration manually
alembic revision --autogenerate -m "description"
```

### Testing
The project uses pytest for testing (installed as dependency). As part of the Clean Architecture refactor, comprehensive tests are being added:

```bash
# Run all tests
pytest

# Run domain layer tests only
pytest tests/domain/

# Run tests with coverage
pytest --cov=domain --cov=application --cov=infrastructure

# Run specific test file
pytest tests/domain/test_tenant_entity.py -v
```

### Clean Architecture Development Workflow

```bash
# Before starting work, understand the refactor plan
cat planning/README.md

# For new features, follow Clean Architecture patterns
# 1. Start with domain entities
# 2. Add use cases in application layer  
# 3. Implement repository interfaces
# 4. Create controllers that use use cases

# Generate migrations during refactor
./generate-migration-test.sh "add new clean architecture tables"

# Verify no breaking changes during refactor
pytest tests/api/ # API integration tests
```

## Code Architecture

### Current Legacy Structure
- **main.py**: FastAPI application entry point with CORS middleware, router registration, and automatic migration handling
- **models/**: Data models using SQLModel for database schema and Pydantic schemas for API validation
- **controller/**: API route handlers organized by domain (tenants, users, auth)
- **database/**: Database connection management and DAO (Data Access Object) layer
- **auth/**: Authentication and authorization using Google OAuth2 with JWT tokens

### New Clean Architecture Structure (In Progress)

Following the four-layer Clean Architecture pattern:

**🎯 Domain Layer** (`domain/`)
- **entities/**: Core business objects with business logic (TenantEntity, OrganizationEntity)
- **repositories/**: Abstract interfaces for data access
- **services/**: Domain services for business logic spanning multiple entities
- **exceptions/**: Business-specific error types

**⚙️ Application Layer** (`application/`) 
- **use_cases/**: Business operations orchestration (CreateTenant, AdmitTenant)
- **dtos/**: Data transfer objects for input/output
- **services/**: Application services coordinating domain objects
- **interfaces/**: Ports for external dependencies

**🔧 Infrastructure Layer** (`infrastructure/`)
- **repositories/**: Concrete repository implementations (SQLTenantRepository)
- **auth/**: Authentication service implementations
- **external/**: Third-party service integrations (S3, email)
- **persistence/**: Database models and migrations

**🌐 Presentation Layer** (`presentation/`)
- **controllers/**: HTTP controllers using dependency injection
- **middleware/**: Cross-cutting concerns (logging, auth)
- **serializers/**: Request/response serialization

### Authentication System
The application uses a role-based access control system with OAuth2/JWT:
- **Roles**: `admin`, `owner` (RCF management), `scworker` (social workers), `pending` (new users)
- **Scopes**: Fine-grained permissions for different operations (view/write for tenants, waitlist, documents, etc.)
- **Authentication Flow**: Google OAuth2 → JWT token with embedded scopes → Role-based route protection

Key files:
- `authentication.py`: JWT token handling and user authorization logic
- `scopes.py`: Role-to-scope mappings and available permissions
- `auth/auth.py`: OAuth2 routes and role assignment

### Database Layer
- **SQLModel**: Combines SQLAlchemy and Pydantic for type-safe database operations
- **Models**: Organization, Tenant, User, Document entities with proper foreign key relationships
- **DAOs**: Data access objects in `database/` folder handle all database operations
- **Migrations**: Alembic for database schema versioning

### Document Management
- File upload/download functionality integrated with AWS S3 (boto3)
- PDF handling for tenant admission documents
- Document metadata stored in database with S3 URLs

### Docker Configuration
- **compose.yml**: Production environment with persistent PostgreSQL data
- **compose.test.yml**: Test environment with ephemeral database and initialization scripts
- Automatic database initialization and migration running on container startup

## Key Patterns

### Controller Pattern
All API endpoints follow a consistent pattern:
- Route definition with appropriate tags for OpenAPI documentation
- Dependency injection for database sessions
- Security dependencies for authentication and authorization
- DAO layer separation for database operations

### Role-Based Security
Routes are protected using the `Security` dependency with required scopes:
```python
user: User = Security(get_current_user_with_scopes, scopes=["write:tenants"])
```

### Environment Configuration
Configuration uses environment variables loaded via python-dotenv:
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`, `JWT_ALGO`: JWT configuration
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: OAuth2 credentials
- AWS credentials for S3 integration

## Development Notes

### Database Connection
The application expects a `DB_URL` environment variable for database connection. The Docker Compose files set up PostgreSQL automatically with the correct connection strings.

### Migration Strategy
- Migrations run automatically on application startup if `DATABASE_URL` is set
- Use the test environment for migration generation to avoid affecting development data
- The `generate-migration-test.sh` script handles running migrations in the correct container context

### CORS Configuration
Currently configured for `www.vacancyportal.ca` domain - adjust in `main.py` for different environments.

## Dependencies
- **FastAPI**: Web framework with automatic OpenAPI documentation
- **SQLModel**: Type-safe ORM built on SQLAlchemy and Pydantic  
- **Alembic**: Database migration tool
- **Authentication**: python-jose for JWT, fastapi-sso for Google OAuth2, bcrypt for password hashing
- **Cloud**: boto3 for AWS S3 integration
- **Database**: psycopg2-binary for PostgreSQL connectivity
- **Testing**: pytest for unit testing framework
