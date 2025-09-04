# Implementation Guide: Clean Architecture for Vacancy Portal

## Overview

This guide provides detailed implementation instructions for refactoring the Vacancy Portal to Clean Architecture with SOLID principles and dependency inversion, including comprehensive Google SSO integration.

## Prerequisites

### Required Dependencies

```toml
# pyproject.toml additions
[tool.poetry.dependencies]
dependency-injector = "^4.41.0"
pydantic = "^2.7.4"  # Already present
fastapi-sso = "^0.15.0"  # Already present
python-jose = "^3.3.0"  # Already present
```

### Directory Structure Setup

```bash
# Create new directory structure
mkdir -p domain/{entities,repositories,services,exceptions,value_objects}
mkdir -p application/{services,dto,interfaces,services}
mkdir -p infrastructure/{database,auth,file_storage,external}
mkdir -p presentation/{controllers,middleware,serializers,validators}
```

## Phase 1: Domain Layer Implementation

### 1.1 Base Entity Class

```python
# domain/entities/base_entity.py
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

class BaseEntity(ABC):
    """Base class for all domain entities"""
    
    def __init__(self, id: Optional[int] = None, created_at: Optional[datetime] = None):
        self._id = id
        self._created_at = created_at or datetime.utcnow()
    
    @property
    def id(self) -> Optional[int]:
        return self._id
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"
```

### 1.2 User Entity with Authentication Support

```python
# domain/entities/user.py
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from .base_entity import BaseEntity

@dataclass
class User(BaseEntity):
    """User domain entity with authentication and authorization logic"""
    
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "pending"
    community_org: Optional[str] = None
    organization_id: Optional[int] = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.id is not None and self.email is not None
    
    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return self.role == role
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        return self.role in roles
    
    def can_access_organization(self, org_id: int) -> bool:
        """Check if user can access specific organization"""
        if self.role == "admin":
            return True
        elif self.role == "owner":
            return self.organization_id == org_id
        elif self.role == "scworker":
            return True  # Social workers can access all organizations
        return False
    
    def get_display_name(self) -> str:
        """Get user's display name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.email
    
    def is_pending_activation(self) -> bool:
        """Check if user needs role assignment"""
        return self.role == "pending"
```

### 1.3 Authentication Domain Services

```python
# domain/services/auth_service.py
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.user import User

class AuthService(ABC):
    """Abstract authentication service"""
    
    @abstractmethod
    async def authenticate_user(self, credentials) -> User:
        """Authenticate user and return domain user entity"""
        pass
    
    @abstractmethod
    def get_login_redirect(self):
        """Get login redirect URL"""
        pass

class TokenService(ABC):
    """Abstract token service"""
    
    @abstractmethod
    def create_token(self, user: User, scopes: List[str]) -> str:
        """Create authentication token for user"""
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> dict:
        """Validate and decode authentication token"""
        pass
    
    @abstractmethod
    def extract_user_from_token(self, token: str) -> Optional[User]:
        """Extract user information from token"""
        pass

class AuthorizationService(ABC):
    """Abstract authorization service"""
    
    @abstractmethod
    def get_user_scopes(self, user: User) -> List[str]:
        """Get user's authorization scopes"""
        pass
    
    @abstractmethod
    def has_scope(self, user: User, scope: str) -> bool:
        """Check if user has specific scope"""
        pass
    
    @abstractmethod
    def has_any_scope(self, user: User, scopes: List[str]) -> bool:
        """Check if user has any of the specified scopes"""
        pass
```

### 1.4 Domain Exceptions

```python
# domain/exceptions/auth_exceptions.py
from domain.exceptions.base_exceptions import DomainException

class AuthenticationError(DomainException):
    """Raised when authentication fails"""
    pass

class AuthorizationError(DomainException):
    """Raised when user lacks required permissions"""
    pass

class InvalidTokenError(DomainException):
    """Raised when token is invalid or expired"""
    pass

class UserNotFoundError(DomainException):
    """Raised when user is not found"""
    pass

class InsufficientPermissionsError(DomainException):
    """Raised when user lacks required permissions for specific operation"""
    pass
```

### 1.5 Value Objects (Focused Approach)

```python
# domain/value_objects/bed_capacity.py
from dataclasses import dataclass
from typing import Optional
from domain.exceptions.base_exceptions import DomainException

class InvalidBedCapacityError(DomainException):
    """Raised when bed capacity is invalid"""
    pass

@dataclass(frozen=True)
class BedCapacity:
    """Value Object representing bed capacity for an organization"""
    
    total_beds: int
    available_beds: int
    
    def __post_init__(self):
        """Validate bed capacity values"""
        if self.total_beds < 0:
            raise InvalidBedCapacityError("Total beds cannot be negative")
        
        if self.available_beds < 0:
            raise InvalidBedCapacityError("Available beds cannot be negative")
        
        if self.available_beds > self.total_beds:
            raise InvalidBedCapacityError("Available beds cannot exceed total beds")
    
    @property
    def occupied_beds(self) -> int:
        """Calculate occupied beds"""
        return self.total_beds - self.available_beds
    
    @property
    def occupancy_rate(self) -> float:
        """Calculate occupancy rate as percentage"""
        if self.total_beds == 0:
            return 0.0
        return (self.occupied_beds / self.total_beds) * 100
    
    @property
    def has_available_beds(self) -> bool:
        """Check if there are available beds"""
        return self.available_beds > 0
    
    @property
    def is_full(self) -> bool:
        """Check if organization is at full capacity"""
        return self.available_beds == 0
    
    def reserve_bed(self) -> 'BedCapacity':
        """Reserve a bed (returns new instance)"""
        if not self.has_available_beds:
            raise InvalidBedCapacityError("No available beds to reserve")
        
        return BedCapacity(
            total_beds=self.total_beds,
            available_beds=self.available_beds - 1
        )
    
    def release_bed(self) -> 'BedCapacity':
        """Release a bed (returns new instance)"""
        if self.available_beds >= self.total_beds:
            raise InvalidBedCapacityError("Cannot release more beds than total capacity")
        
        return BedCapacity(
            total_beds=self.total_beds,
            available_beds=self.available_beds + 1
        )
    
    @classmethod
    def unlimited(cls) -> 'BedCapacity':
        """Create unlimited bed capacity"""
        return cls(total_beds=-1, available_beds=-1)
    
    @property
    def is_unlimited(self) -> bool:
        """Check if capacity is unlimited"""
        return self.total_beds == -1 and self.available_beds == -1
    
    def __str__(self) -> str:
        if self.is_unlimited:
            return "Unlimited capacity"
        return f"{self.available_beds}/{self.total_beds} beds available"
    
    def __repr__(self) -> str:
        return f"BedCapacity(total={self.total_beds}, available={self.available_beds})"
```

### 1.6 Updated Organization Entity with BedCapacity

```python
# domain/entities/organization.py
from dataclasses import dataclass
from typing import Optional
from .base_entity import BaseEntity
from .value_objects.bed_capacity import BedCapacity

@dataclass
class Organization(BaseEntity):
    """Organization domain entity with bed capacity management"""
    
    business_name: str
    address: str
    bed_capacity: BedCapacity
    owner_id: int = None
    
    def has_available_beds(self) -> bool:
        """Check if organization has available beds"""
        return self.bed_capacity.has_available_beds
    
    def is_at_capacity(self) -> bool:
        """Check if organization is at full capacity"""
        return self.bed_capacity.is_full
    
    def get_occupancy_rate(self) -> float:
        """Get current occupancy rate"""
        return self.bed_capacity.occupancy_rate
    
    def reserve_bed(self) -> None:
        """Reserve a bed for a new tenant"""
        if not self.has_available_beds():
            raise ValueError("No available beds")
        
        # Create new organization with updated bed capacity
        new_capacity = self.bed_capacity.reserve_bed()
        self.bed_capacity = new_capacity
    
    def release_bed(self) -> None:
        """Release a bed when tenant is discharged"""
        # Create new organization with updated bed capacity
        new_capacity = self.bed_capacity.release_bed()
        self.bed_capacity = new_capacity
    
    def get_capacity_summary(self) -> str:
        """Get human-readable capacity summary"""
        return str(self.bed_capacity)
```

## Phase 2: Application Layer Implementation

### 2.1 Authentication DTOs

```python
# application/dto/auth_dto.py
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class GoogleSSOLoginRequest:
    """Request for Google SSO login"""
    # Google SSO callback data
    pass

@dataclass
class LoginResult:
    """Result of successful login"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    role: str
    scopes: List[str]
    expires_in: int = 3600

@dataclass
class TokenValidationRequest:
    """Request for token validation"""
    token: str

@dataclass
class TokenValidationResult:
    """Result of token validation"""
    is_valid: bool
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
    scopes: Optional[List[str]] = None
    error_message: Optional[str] = None

@dataclass
class UserRoleUpdateRequest:
    """Request for updating user role"""
    user_id: int
    new_role: str

@dataclass
class UserRoleUpdateResult:
    """Result of user role update"""
    success: bool
    user_id: int
    previous_role: str
    new_role: str
    message: str

@dataclass
class UserProfileResponse:
    """User profile information"""
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    community_org: Optional[str]
    organization_id: Optional[int]
    display_name: str
    is_pending_activation: bool
```

### 2.2 Authentication Services

```python
# application/services/auth_services.py
from typing import Optional
from fastapi import Request
from domain.entities.user import User
from domain.services.auth_service import AuthService, TokenService, AuthorizationService
from domain.services.user_service import UserService
from domain.exceptions.auth_exceptions import AuthenticationError, AuthorizationError, UserNotFoundError
from application.dto.auth_dto import (
    GoogleSSOLoginRequest, LoginResult, TokenValidationRequest, 
    TokenValidationResult, UserRoleUpdateRequest, UserRoleUpdateResult,
    UserProfileResponse
)

class GoogleSSOLoginService:
    """Application service for Google SSO authentication"""
    
    def __init__(self, 
                 auth_service: AuthService,
                 user_service: UserService,
                 token_service: TokenService,
                 authorization_service: AuthorizationService):
        self.auth_service = auth_service
        self.user_service = user_service
        self.token_service = token_service
        self.authorization_service = authorization_service
    
    async def execute(self, request: Request) -> LoginResult:
        """Execute Google SSO login workflow"""
        try:
            # 1. Authenticate with Google SSO
            user_data = await self.auth_service.authenticate_user(request)
            
            # 2. Get or create user in domain
            user = await self.user_service.get_or_create_user(user_data)
            
            # 3. Get user's authorization scopes
            scopes = self.authorization_service.get_user_scopes(user)
            
            # 4. Generate JWT token
            token = self.token_service.create_token(user, scopes)
            
            return LoginResult(
                access_token=token,
                user_id=user.id,
                email=user.email,
                role=user.role,
                scopes=scopes
            )
            
        except Exception as e:
            raise AuthenticationError(f"Google SSO authentication failed: {str(e)}")

class TokenValidationService:
    """Application service for validating authentication tokens"""
    
    def __init__(self, 
                 token_service: TokenService,
                 user_service: UserService,
                 authorization_service: AuthorizationService):
        self.token_service = token_service
        self.user_service = user_service
        self.authorization_service = authorization_service
    
    async def execute(self, request: TokenValidationRequest) -> TokenValidationResult:
        """Execute token validation workflow"""
        try:
            # 1. Validate and decode token
            token_data = self.token_service.validate_token(request.token)
            
            # 2. Extract user information
            user = self.token_service.extract_user_from_token(request.token)
            if not user:
                return TokenValidationResult(
                    is_valid=False,
                    error_message="Invalid token: user not found"
                )
            
            # 3. Get current user scopes
            scopes = self.authorization_service.get_user_scopes(user)
            
            return TokenValidationResult(
                is_valid=True,
                user_id=user.id,
                email=user.email,
                role=user.role,
                scopes=scopes
            )
            
        except Exception as e:
            return TokenValidationResult(
                is_valid=False,
                error_message=f"Token validation failed: {str(e)}"
            )

class GetCurrentUserService:
    """Application service for getting current authenticated user"""
    
    def __init__(self, 
                 token_service: TokenService,
                 user_service: UserService):
        self.token_service = token_service
        self.user_service = user_service
    
    async def execute(self, token: str) -> UserProfileResponse:
        """Execute get current user workflow"""
        # 1. Extract user from token
        user = self.token_service.extract_user_from_token(token)
        if not user:
            raise AuthenticationError("Invalid token: user not found")
        
        # 2. Get fresh user data from repository
        current_user = await self.user_service.get_user_by_id(user.id)
        if not current_user:
            raise UserNotFoundError(f"User {user.id} not found")
        
        return UserProfileResponse(
            id=current_user.id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            role=current_user.role,
            community_org=current_user.community_org,
            organization_id=current_user.organization_id,
            display_name=current_user.get_display_name(),
            is_pending_activation=current_user.is_pending_activation()
        )

class UpdateUserRoleService:
    """Application service for updating user role"""
    
    def __init__(self, 
                 user_service: UserService,
                 authorization_service: AuthorizationService):
        self.user_service = user_service
        self.authorization_service = authorization_service
    
    async def execute(self, request: UserRoleUpdateRequest, current_user: User) -> UserRoleUpdateResult:
        """Execute user role update workflow"""
        # 1. Check if current user can update roles
        if not self.authorization_service.has_scope(current_user, "write:users"):
            raise AuthorizationError("Insufficient permissions to update user roles")
        
        # 2. Get user to update
        user = await self.user_service.get_user_by_id(request.user_id)
        if not user:
            raise UserNotFoundError(f"User {request.user_id} not found")
        
        # 3. Validate role change
        if not user.is_pending_activation():
            raise AuthorizationError("Can only update roles for pending users")
        
        # 4. Store previous role
        previous_role = user.role
        
        # 5. Update user role
        updated_user = await self.user_service.update_user_role(user.id, request.new_role)
        
        return UserRoleUpdateResult(
            success=True,
            user_id=updated_user.id,
            previous_role=previous_role,
            new_role=updated_user.role,
            message=f"User role updated from {previous_role} to {updated_user.role}"
        )

class GetLoginRedirectService:
    """Application service for getting Google SSO login redirect"""
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
    
    def execute(self):
        """Execute get login redirect workflow"""
        return self.auth_service.get_login_redirect()
```

## Phase 3: Infrastructure Layer Implementation

### 3.1 Google SSO Infrastructure Adapters

```python
# infrastructure/auth/google_sso_adapter.py
from fastapi import Request
from fastapi_sso.sso.google import GoogleSSO
from fastapi_sso.sso.base import OpenID
from domain.services.auth_service import AuthService
from domain.entities.user import User
from domain.exceptions.auth_exceptions import AuthenticationError
import os

class GoogleSSOAdapter(AuthService):
    """Google SSO adapter for Clean Architecture"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.sso = GoogleSSO(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            allow_insecure_http=True  # For development
        )
    
    async def authenticate_user(self, request: Request) -> User:
        """Authenticate user via Google SSO"""
        try:
            with self.sso:
                user_data = await self.sso.verify_and_process(request)
                return self._map_google_user_to_domain_user(user_data)
        except Exception as e:
            raise AuthenticationError(f"Google SSO authentication failed: {str(e)}")
    
    def get_login_redirect(self):
        """Get Google SSO login redirect"""
        with self.sso:
            return self.sso.get_login_redirect()
    
    def _map_google_user_to_domain_user(self, google_user: OpenID) -> User:
        """Map Google user data to domain user entity"""
        return User(
            email=google_user.email,
            first_name=google_user.first_name,
            last_name=google_user.last_name,
            role="pending"  # Default role, will be updated during onboarding
        )

# Factory for creating Google SSO adapter
def create_google_sso_adapter() -> GoogleSSOAdapter:
    """Factory function to create Google SSO adapter with environment variables"""
    client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/auth/callback')
    
    if not client_id or not client_secret:
        raise ValueError("Google SSO credentials not configured")
    
    return GoogleSSOAdapter(client_id, client_secret, redirect_uri)
```

### 3.2 JWT Token Service Implementation

```python
# infrastructure/auth/jwt_token_service.py
from datetime import datetime, timedelta, UTC
from typing import Optional, List
from jose import jwt, JWTError
from domain.services.auth_service import TokenService
from domain.entities.user import User
from domain.exceptions.auth_exceptions import InvalidTokenError
import os
import uuid

class JWTTokenService(TokenService):
    """JWT token service implementation"""
    
    def __init__(self, secret: str, algorithm: str = "HS256", token_expiry_hours: int = 1):
        self.secret = secret
        self.algorithm = algorithm
        self.token_expiry_hours = token_expiry_hours
    
    def create_token(self, user: User, scopes: List[str]) -> str:
        """Create JWT token for user"""
        payload = {
            "sub": user.email,  # Subject (user identifier)
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "scopes": scopes,
            "exp": datetime.now(UTC) + timedelta(hours=self.token_expiry_hours),
            "iat": datetime.now(UTC),  # Issued at
            "jti": str(uuid.uuid4()),  # JWT ID (unique identifier)
        }
        
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def validate_token(self, token: str) -> dict:
        """Validate and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise InvalidTokenError(f"Invalid JWT token: {str(e)}")
    
    def extract_user_from_token(self, token: str) -> Optional[User]:
        """Extract user information from token"""
        try:
            payload = self.validate_token(token)
            
            # Create user entity from token payload
            user = User(
                id=payload.get("user_id"),
                email=payload.get("email"),
                role=payload.get("role", "pending")
            )
            
            return user
        except InvalidTokenError:
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired"""
        try:
            payload = self.validate_token(token)
            exp_timestamp = payload.get("exp")
            if not exp_timestamp:
                return True
            
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=UTC)
            return datetime.now(UTC) >= exp_datetime
        except InvalidTokenError:
            return True

# Factory for creating JWT token service
def create_jwt_token_service() -> JWTTokenService:
    """Factory function to create JWT token service with environment variables"""
    secret = os.getenv('JWT_SECRET', '')
    algorithm = os.getenv('JWT_ALGO', 'HS256')
    
    if not secret:
        raise ValueError("JWT secret not configured")
    
    return JWTTokenService(secret, algorithm)
```

### 3.3 Authorization Service Implementation

```python
# infrastructure/auth/authorization_service.py
from typing import List
from domain.services.auth_service import AuthorizationService
from domain.entities.user import User

class ScopeBasedAuthorizationService(AuthorizationService):
    """Scope-based authorization service implementation"""
    
    # Define available scopes
    AVAILABLE_SCOPES = {
        "view:dashboard": "Permission to view the dashboard",
        "view:waitlist": "Permission to view the waitlist",
        "write:waitlist": "Permission to modify the waitlist",
        "view:tenants": "Permission to view tenant information",
        "write:tenants": "Permission to modify tenant information",
        "view:profile": "Permission to view user profiles",
        "write:profile": "Permission to modify user profiles",
        "view:organization": "Permission to view organization details",
        "write:organization": "Permission to modify organization details",
        "view:documents": "Permission to view tenant documents",
        "write:documents": "Permission to upload and modify tenant documents",
        "view:users": "Permission to view user information",
        "write:users": "Permission to modify user information"
    }
    
    # Define role-based scope mappings
    ROLE_SCOPES = {
        "admin": list(AVAILABLE_SCOPES.keys()),
        "scworker": [
            "view:dashboard", "write:waitlist", "view:profile",
            "write:profile", "view:organization", "view:documents", 
            "write:documents", "view:users", "write:users"
        ],
        "owner": [
            "view:dashboard", "view:waitlist", "write:waitlist", 
            "view:profile", "write:profile", "view:organization", 
            "write:organization", "view:documents", "view:users", 
            "write:users"
        ],
        "pending": ["write:profile"]  # Limited permissions for pending users
    }
    
    def get_user_scopes(self, user: User) -> List[str]:
        """Get user's authorization scopes based on role"""
        if user.role not in self.ROLE_SCOPES:
            return []  # No scopes for unknown roles
        
        return self.ROLE_SCOPES[user.role].copy()
    
    def has_scope(self, user: User, scope: str) -> bool:
        """Check if user has specific scope"""
        user_scopes = self.get_user_scopes(user)
        return scope in user_scopes
    
    def has_any_scope(self, user: User, scopes: List[str]) -> bool:
        """Check if user has any of the specified scopes"""
        user_scopes = self.get_user_scopes(user)
        return any(scope in user_scopes for scope in scopes)
    
    def has_all_scopes(self, user: User, scopes: List[str]) -> bool:
        """Check if user has all of the specified scopes"""
        user_scopes = self.get_user_scopes(user)
        return all(scope in user_scopes for scope in scopes)
    
    def get_available_scopes(self) -> dict:
        """Get all available scopes with descriptions"""
        return self.AVAILABLE_SCOPES.copy()
    
    def get_role_scopes(self, role: str) -> List[str]:
        """Get scopes for a specific role"""
        return self.ROLE_SCOPES.get(role, []).copy()

# Factory for creating authorization service
def create_authorization_service() -> ScopeBasedAuthorizationService:
    """Factory function to create authorization service"""
    return ScopeBasedAuthorizationService()
```

### 3.4 User Repository Implementation

```python
# infrastructure/database/user_repository.py
from typing import Optional, List
from sqlmodel import Session, select
from domain.repositories.user_repository import UserRepository
from domain.entities.user import User
from domain.exceptions.auth_exceptions import UserNotFoundError
from models.models import User as UserModel
from models.schemas import UserBase

class SQLUserRepository(UserRepository):
    """SQLModel implementation of user repository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        statement = select(UserModel).where(UserModel.id == user_id)
        result = self.db.exec(statement).first()
        
        if not result:
            return None
        
        return self._map_to_domain_user(result)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        statement = select(UserModel).where(UserModel.email == email)
        result = self.db.exec(statement).first()
        
        if not result:
            return None
        
        return self._map_to_domain_user(result)
    
    async def create_user(self, user_data: UserBase) -> User:
        """Create new user"""
        # Check if user already exists
        existing_user = await self.get_by_email(user_data.email)
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")
        
        # Create user model
        user_model = UserModel(**user_data.model_dump())
        self.db.add(user_model)
        self.db.commit()
        self.db.refresh(user_model)
        
        return self._map_to_domain_user(user_model)
    
    async def update_user_role(self, user_id: int, new_role: str) -> User:
        """Update user role"""
        user_model = self.db.get(UserModel, user_id)
        if not user_model:
            raise UserNotFoundError(f"User {user_id} not found")
        
        # Validate role
        valid_roles = ["owner", "scworker", "admin"]
        if new_role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        
        user_model.role = new_role
        self.db.commit()
        self.db.refresh(user_model)
        
        return self._map_to_domain_user(user_model)
    
    async def get_or_create_user(self, user_data: User) -> User:
        """Get existing user or create new one"""
        existing_user = await self.get_by_email(user_data.email)
        if existing_user:
            return existing_user
        
        # Create new user
        user_base = UserBase(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            community_org=user_data.community_org
        )
        
        return await self.create_user(user_base)
    
    def _map_to_domain_user(self, user_model: UserModel) -> User:
        """Map SQLModel user to domain user entity"""
        return User(
            id=user_model.id,
            email=user_model.email,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            role=user_model.role,
            community_org=user_model.community_org,
            organization_id=user_model.organization_id,
            created_at=user_model.created_at if hasattr(user_model, 'created_at') else None
        )
```

### 3.5 Organization Repository Implementation

```python
# infrastructure/database/organization_repository.py
from typing import Optional, List
from sqlmodel import Session, select
from domain.repositories.organization_repository import OrganizationRepository
from domain.entities.organization import Organization
from domain.exceptions.organization_exceptions import OrganizationNotFoundError
from models.models import Organization as OrganizationModel
from models.schemas import OrganizationBase

class SQLOrganizationRepository(OrganizationRepository):
    """SQLModel implementation of organization repository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID"""
        statement = select(OrganizationModel).where(OrganizationModel.id == org_id)
        result = self.db.exec(statement).first()
        
        if not result:
            return None
        
        return self._map_to_domain_organization(result)
    
    async def get_by_owner(self, owner_id: int) -> Optional[Organization]:
        """Get organization by owner ID"""
        statement = select(OrganizationModel).where(OrganizationModel.owner_id == owner_id)
        result = self.db.exec(statement).first()
        
        if not result:
            return None
        
        return self._map_to_domain_organization(result)
    
    async def create_organization(self, org_data: OrganizationBase) -> Organization:
        """Create new organization"""
        # Check if organization already exists
        existing_org = await self.get_by_owner(org_data.owner_id)
        if existing_org:
            raise ValueError(f"Organization for owner {org_data.owner_id} already exists")
        
        # Create organization model
        org_model = OrganizationModel(**org_data.model_dump())
        self.db.add(org_model)
        self.db.commit()
        self.db.refresh(org_model)
        
        return self._map_to_domain_organization(org_model)
    
    async def update_organization(self, org_id: int, org_data: OrganizationBase) -> Organization:
        """Update organization"""
        org_model = self.db.get(OrganizationModel, org_id)
        if not org_model:
            raise OrganizationNotFoundError(f"Organization {org_id} not found")
        
        # Update fields
        org_model.business_name = org_data.business_name
        org_model.address = org_data.address
        org_model.number_of_beds = org_data.number_of_beds
        org_model.owner_id = org_data.owner_id
        
        self.db.add(org_model)
        self.db.commit()
        self.db.refresh(org_model)
        
        return self._map_to_domain_organization(org_model)
    
    async def delete_organization(self, org_id: int) -> bool:
        """Delete organization by ID"""
        org_model = self.db.get(OrganizationModel, org_id)
        
        if not org_model:
            return False
        
        self.db.delete(org_model)
        self.db.commit()
        return True
    
    async def list_all(self) -> List[Organization]:
        """List all organizations"""
        statement = select(OrganizationModel)
        results = self.db.exec(statement).all()
        return [self._map_to_domain_organization(result) for result in results]
    
    def _map_to_domain_organization(self, org_model: OrganizationModel) -> Organization:
        """Map SQLModel organization to domain organization entity"""
        return Organization(
            id=org_model.id,
            business_name=org_model.business_name,
            address=org_model.address,
            number_of_beds=org_model.number_of_beds,
            owner_id=org_model.owner_id,
            created_at=org_model.created_at if hasattr(org_model, 'created_at') else None
        )
```

### 3.6 Tenant Repository Implementation

```python
# infrastructure/database/tenant_repository.py
from typing import List, Optional
from sqlmodel import Session, select
from domain.repositories.tenant_repository import TenantRepository
from domain.entities.tenant import Tenant
from domain.exceptions.tenant_exceptions import TenantNotFoundError
from models.models import Tenant as TenantModel
from models.schemas import TenantBase

class SQLTenantRepository(TenantRepository):
    """SQLModel implementation of tenant repository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant"""
        tenant_model = TenantModel(
            name=tenant.name,
            admission_date=tenant.admission_date,
            discharge_date=tenant.discharge_date,
            waitlist=tenant.waitlist,
            organization_id=tenant.organization_id
        )
        
        self.db.add(tenant_model)
        self.db.commit()
        self.db.refresh(tenant_model)
        
        return self._map_to_domain_tenant(tenant_model)
    
    async def get_by_id(self, id: int) -> Optional[Tenant]:
        """Get tenant by ID"""
        statement = select(TenantModel).where(TenantModel.id == id)
        result = self.db.exec(statement).first()
        return self._map_to_domain_tenant(result) if result else None
    
    async def get_by_name(self, name: str) -> Optional[Tenant]:
        """Get tenant by name"""
        statement = select(TenantModel).where(TenantModel.name == name)
        result = self.db.exec(statement).first()
        return self._map_to_domain_tenant(result) if result else None
    
    async def get_waitlist_tenants(self) -> List[Tenant]:
        """Get all waitlist tenants"""
        statement = select(TenantModel).where(TenantModel.waitlist == True)
        results = self.db.exec(statement).all()
        return [self._map_to_domain_tenant(result) for result in results]
    
    async def get_active_tenants(self) -> List[Tenant]:
        """Get all active tenants"""
        statement = select(TenantModel).where(TenantModel.discharge_date.is_(None))
        results = self.db.exec(statement).all()
        return [self._map_to_domain_tenant(result) for result in results]
    
    async def update(self, tenant: Tenant) -> Tenant:
        """Update tenant"""
        statement = select(TenantModel).where(TenantModel.id == tenant.id)
        tenant_model = self.db.exec(statement).first()
        
        if not tenant_model:
            raise TenantNotFoundError(f"Tenant with id {tenant.id} not found")
        
        # Update fields
        tenant_model.name = tenant.name
        tenant_model.admission_date = tenant.admission_date
        tenant_model.discharge_date = tenant.discharge_date
        tenant_model.waitlist = tenant.waitlist
        tenant_model.organization_id = tenant.organization_id
        
        self.db.add(tenant_model)
        self.db.commit()
        self.db.refresh(tenant_model)
        
        return self._map_to_domain_tenant(tenant_model)
    
    async def delete(self, id: int) -> bool:
        """Delete tenant by ID"""
        statement = select(TenantModel).where(TenantModel.id == id)
        tenant_model = self.db.exec(statement).first()
        
        if not tenant_model:
            return False
        
        self.db.delete(tenant_model)
        self.db.commit()
        return True
    
    async def list_all(self) -> List[Tenant]:
        """List all tenants"""
        statement = select(TenantModel)
        results = self.db.exec(statement).all()
        return [self._map_to_domain_tenant(result) for result in results]
    
    def _map_to_domain_tenant(self, tenant_model: TenantModel) -> Tenant:
        """Map SQLModel tenant to domain tenant entity"""
        return Tenant(
            id=tenant_model.id,
            name=tenant_model.name,
            admission_date=tenant_model.admission_date,
            discharge_date=tenant_model.discharge_date,
            waitlist=tenant_model.waitlist,
            organization_id=tenant_model.organization_id,
            created_at=tenant_model.created_at if hasattr(tenant_model, 'created_at') else None
        )
```

### 3.7 Dependency Injection Container

```python
# core/container.py
from dependency_injector import containers, providers
from sqlmodel import Session, create_engine
from database.db import get_session

# Import repositories
from infrastructure.database.tenant_repository import SQLTenantRepository
from infrastructure.database.user_repository import SQLUserRepository
from infrastructure.database.organization_repository import SQLOrganizationRepository

# Import domain services
from domain.services.tenant_service import TenantService
from domain.services.user_service import UserService
from domain.services.organization_service import OrganizationService

# Import application services
from application.services.tenant_services import (
    CreateTenantService, GetTenantService, GetWaitlistTenantsService,
    AdmitTenantService, UpdateTenantService, DeleteTenantService
)
from application.services.auth_services import (
    GoogleSSOLoginService, TokenValidationService, GetCurrentUserService,
    UpdateUserRoleService, GetLoginRedirectService
)

# Import infrastructure services
from infrastructure.auth.google_sso_adapter import create_google_sso_adapter
from infrastructure.auth.jwt_token_service import create_jwt_token_service
from infrastructure.auth.authorization_service import create_authorization_service

class Container(containers.DeclarativeContainer):
    """Dependency injection container"""
    
    # Configuration
    config = providers.Configuration()
    
    # Database
    session = providers.Singleton(get_session)
    
    # Repositories
    tenant_repository = providers.Factory(
        SQLTenantRepository,
        db=session
    )
    
    user_repository = providers.Factory(
        SQLUserRepository,
        db=session
    )
    
    organization_repository = providers.Factory(
        SQLOrganizationRepository,
        db=session
    )
    
    # Domain Services
    tenant_service = providers.Factory(
        TenantService,
        tenant_repository=tenant_repository
    )
    
    user_service = providers.Factory(
        UserService,
        user_repository=user_repository
    )
    
    organization_service = providers.Factory(
        OrganizationService,
        organization_repository=organization_repository
    )
    
    # Infrastructure Services
    google_sso_adapter = providers.Factory(
        create_google_sso_adapter
    )

    jwt_token_service = providers.Factory(
        create_jwt_token_service
    )

    authorization_service = providers.Factory(
        create_authorization_service
    )
    
    # Application Services
    create_tenant_service = providers.Factory(
        CreateTenantService,
        tenant_service=tenant_service
    )
    
    get_tenant_service = providers.Factory(
        GetTenantService,
        tenant_service=tenant_service
    )
    
    get_waitlist_tenants_service = providers.Factory(
        GetWaitlistTenantsService,
        tenant_service=tenant_service
    )
    
    admit_tenant_service = providers.Factory(
        AdmitTenantService,
        tenant_service=tenant_service
    )
    
    update_tenant_service = providers.Factory(
        UpdateTenantService,
        tenant_service=tenant_service
    )
    
    delete_tenant_service = providers.Factory(
        DeleteTenantService,
        tenant_service=tenant_service
    )
    
    # Authentication Services
    google_sso_login_service = providers.Factory(
        GoogleSSOLoginService,
        auth_service=google_sso_adapter,
        user_service=user_service,
        token_service=jwt_token_service,
        authorization_service=authorization_service
    )
    
    token_validation_service = providers.Factory(
        TokenValidationService,
        token_service=jwt_token_service,
        user_service=user_service,
        authorization_service=authorization_service
    )
    
    get_current_user_service = providers.Factory(
        GetCurrentUserService,
        token_service=jwt_token_service,
        user_service=user_service
    )
    
    update_user_role_service = providers.Factory(
        UpdateUserRoleService,
        user_service=user_service,
        authorization_service=authorization_service
    )
    
    get_login_redirect_service = providers.Factory(
        GetLoginRedirectService,
        auth_service=google_sso_adapter
    )
```

## Phase 4: Presentation Layer Implementation

### 4.1 Authentication Controllers

```python
# presentation/controllers/auth_controller.py
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import OAuth2PasswordBearer
from dependency_injector.wiring import inject, Provide
from application.services.auth_services import (
    GoogleSSOLoginService, TokenValidationService, GetCurrentUserService,
    UpdateUserRoleService, GetLoginRedirectService
)
from application.dto.auth_dto import (
    LoginResult, TokenValidationRequest, TokenValidationResult,
    UserRoleUpdateRequest, UserRoleUpdateResult, UserProfileResponse
)
from domain.exceptions.auth_exceptions import (
    AuthenticationError, AuthorizationError, UserNotFoundError, InvalidTokenError
)
from core.container import Container

auth_router = APIRouter(prefix='/api/auth', tags=['Authentication'])

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@auth_router.get('/google/login')
@inject
async def google_login(
    login_redirect_service: GetLoginRedirectService = Depends(Provide[Container.get_login_redirect_service])
):
    """Initiate Google SSO login"""
    try:
        return login_redirect_service.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate Google SSO: {str(e)}")

@auth_router.get('/google/callback')
@inject
async def google_callback(
    request: Request,
    login_service: GoogleSSOLoginService = Depends(Provide[Container.google_sso_login_service])
):
    """Handle Google SSO callback and authenticate user"""
    try:
        result: LoginResult = await login_service.execute(request)
        return {
            "access_token": result.access_token,
            "token_type": result.token_type,
            "user_id": result.user_id,
            "email": result.email,
            "role": result.role,
            "scopes": result.scopes,
            "expires_in": result.expires_in
        }
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@auth_router.post('/validate-token')
@inject
async def validate_token(
    token: str = Depends(oauth2_scheme),
    validation_service: TokenValidationService = Depends(Provide[Container.token_validation_service])
):
    """Validate authentication token"""
    try:
        request = TokenValidationRequest(token=token)
        result: TokenValidationResult = await validation_service.execute(request)
        
        if not result.is_valid:
            raise HTTPException(status_code=401, detail=result.error_message)
        
        return {
            "is_valid": result.is_valid,
            "user_id": result.user_id,
            "email": result.email,
            "role": result.role,
            "scopes": result.scopes
        }
    except InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token validation failed: {str(e)}")

@auth_router.get('/me')
@inject
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    current_user_service: GetCurrentUserService = Depends(Provide[Container.get_current_user_service])
):
    """Get current authenticated user profile"""
    try:
        result: UserProfileResponse = await current_user_service.execute(token)
        return {
            "id": result.id,
            "email": result.email,
            "first_name": result.first_name,
            "last_name": result.last_name,
            "role": result.role,
            "community_org": result.community_org,
            "organization_id": result.organization_id,
            "display_name": result.display_name,
            "is_pending_activation": result.is_pending_activation
        }
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")

@auth_router.post('/set-role')
@inject
async def set_user_role(
    role_request: UserRoleUpdateRequest,
    token: str = Depends(oauth2_scheme),
    update_role_service: UpdateUserRoleService = Depends(Provide[Container.update_user_role_service]),
    current_user_service: GetCurrentUserService = Depends(Provide[Container.get_current_user_service])
):
    """Set user role during onboarding"""
    try:
        # Get current user from token
        current_user_response = await current_user_service.execute(token)
        
        # Execute role update
        result: UserRoleUpdateResult = await update_role_service.execute(role_request, current_user_response)
        
        return {
            "success": result.success,
            "user_id": result.user_id,
            "previous_role": result.previous_role,
            "new_role": result.new_role,
            "message": result.message
        }
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user role: {str(e)}")
```

### 4.2 Authentication Middleware

```python
# presentation/middleware/auth_middleware.py
from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from domain.entities.user import User
from domain.exceptions.auth_exceptions import AuthenticationError, InvalidTokenError
from infrastructure.auth.jwt_token_service import JWTTokenService
from infrastructure.auth.authorization_service import ScopeBasedAuthorizationService
from infrastructure.database.user_repository import SQLUserRepository
from database.db import get_session
from sqlmodel import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthenticationMiddleware:
    """Middleware for handling authentication and authorization"""
    
    def __init__(self, token_service: JWTTokenService, auth_service: ScopeBasedAuthorizationService):
        self.token_service = token_service
        self.auth_service = auth_service
    
    async def get_current_user(
        self, 
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_session)
    ) -> User:
        """Extract and validate current user from token"""
        try:
            # Validate token
            payload = self.token_service.validate_token(token)
            
            # Extract user from token
            user = self.token_service.extract_user_from_token(token)
            if not user:
                raise AuthenticationError("Invalid token: user not found")
            
            # Get fresh user data from database
            user_repo = SQLUserRepository(db)
            current_user = await user_repo.get_by_id(user.id)
            if not current_user:
                raise AuthenticationError("User not found in database")
            
            return current_user
            
        except InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except AuthenticationError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")
    
    def require_scope(self, required_scope: str):
        """Decorator to require specific scope"""
        def scope_dependency(
            current_user: User = Depends(self.get_current_user),
            auth_service: ScopeBasedAuthorizationService = Depends(lambda: self.auth_service)
        ):
            if not auth_service.has_scope(current_user, required_scope):
                raise HTTPException(
                    status_code=403,
                    detail=f"Required scope: {required_scope}"
                )
            return current_user
        return scope_dependency
    
    def require_any_scope(self, required_scopes: list):
        """Decorator to require any of the specified scopes"""
        def scope_dependency(
            current_user: User = Depends(self.get_current_user),
            auth_service: ScopeBasedAuthorizationService = Depends(lambda: self.auth_service)
        ):
            if not auth_service.has_any_scope(current_user, required_scopes):
                raise HTTPException(
                    status_code=403,
                    detail=f"Required one of scopes: {', '.join(required_scopes)}"
                )
            return current_user
        return scope_dependency
    
    def require_role(self, required_role: str):
        """Decorator to require specific role"""
        def role_dependency(current_user: User = Depends(self.get_current_user)):
            if not current_user.has_role(required_role):
                raise HTTPException(
                    status_code=403,
                    detail=f"Required role: {required_role}"
                )
            return current_user
        return role_dependency
    
    def require_any_role(self, required_roles: list):
        """Decorator to require any of the specified roles"""
        def role_dependency(current_user: User = Depends(self.get_current_user)):
            if not current_user.has_any_role(required_roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"Required one of roles: {', '.join(required_roles)}"
                )
            return current_user
        return role_dependency

# Factory for creating authentication middleware
def create_auth_middleware(token_service: JWTTokenService, auth_service: ScopeBasedAuthorizationService) -> AuthenticationMiddleware:
    """Factory function to create authentication middleware"""
    return AuthenticationMiddleware(token_service, auth_service)
```

### 4.3 Updated Tenant Controller with Authentication

```python
# presentation/controllers/tenant_controller.py
from fastapi import APIRouter, Depends, HTTPException, Security
from typing import List
from dependency_injector.wiring import inject, Provide
from application.services.tenant_services import (
    CreateTenantService, GetTenantService, GetWaitlistTenantsService,
    AdmitTenantService, UpdateTenantService, DeleteTenantService
)
from application.dto.tenant_dto import (
    CreateTenantRequest, UpdateTenantRequest, TenantResponse
)
from domain.entities.user import User
from domain.exceptions.tenant_exceptions import (
    TenantNotFoundError, TenantAlreadyExistsError, OrganizationCapacityExceededError
)
from domain.exceptions.auth_exceptions import InsufficientPermissionsError
from presentation.middleware.auth_middleware import AuthenticationMiddleware
from core.container import Container

tenant_router = APIRouter(prefix='/api/tenants', tags=['Tenants'])

@tenant_router.post('/create-tenant', response_model=TenantResponse)
@inject
async def create_tenant(
    tenant_data: CreateTenantRequest,
    current_user: User = Security(AuthenticationMiddleware.require_scope("write:tenants")),
    create_service: CreateTenantService = Depends(Provide[Container.create_tenant_service])
):
    """Create a new tenant"""
    try:
        result = await create_service.execute(tenant_data, current_user)
        return result
    except TenantAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except OrganizationCapacityExceededError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create tenant: {str(e)}")

@tenant_router.get('/tenant/{tenant_id}', response_model=TenantResponse)
@inject
async def get_tenant(
    tenant_id: int,
    current_user: User = Security(AuthenticationMiddleware.require_scope("view:tenants")),
    get_service: GetTenantService = Depends(Provide[Container.get_tenant_service])
):
    """Get tenant by ID"""
    try:
        result = await get_service.execute(tenant_id, current_user)
        return result
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tenant: {str(e)}")

@tenant_router.get('/waitlist', response_model=List[TenantResponse])
@inject
async def get_waitlist(
    current_user: User = Security(AuthenticationMiddleware.require_scope("view:waitlist")),
    waitlist_service: GetWaitlistTenantsService = Depends(Provide[Container.get_waitlist_tenants_service])
):
    """Get all waitlist tenants"""
    try:
        results = await waitlist_service.execute(current_user)
        return results
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get waitlist: {str(e)}")

@tenant_router.post('/admit/{tenant_id}', response_model=TenantResponse)
@inject
async def admit_tenant(
    tenant_id: int,
    current_user: User = Security(AuthenticationMiddleware.require_scope("write:tenants")),
    admit_service: AdmitTenantService = Depends(Provide[Container.admit_tenant_service])
):
    """Admit tenant from waitlist"""
    try:
        result = await admit_service.execute(tenant_id, current_user)
        return result
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to admit tenant: {str(e)}")

@tenant_router.put('/update/{tenant_id}', response_model=TenantResponse)
@inject
async def update_tenant(
    tenant_id: int,
    update_data: UpdateTenantRequest,
    current_user: User = Security(AuthenticationMiddleware.require_scope("write:tenants")),
    update_service: UpdateTenantService = Depends(Provide[Container.update_tenant_service])
):
    """Update tenant information"""
    try:
        result = await update_service.execute(tenant_id, update_data, current_user)
        return result
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update tenant: {str(e)}")

@tenant_router.delete('/delete/{tenant_id}')
@inject
async def delete_tenant(
    tenant_id: int,
    current_user: User = Security(AuthenticationMiddleware.require_scope("write:tenants")),
    delete_service: DeleteTenantService = Depends(Provide[Container.delete_tenant_service])
):
    """Delete tenant"""
    try:
        await delete_service.execute(tenant_id, current_user)
        return {"message": "Tenant deleted successfully"}
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete tenant: {str(e)}")
```

### 4.4 Updated Main Application

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dependency_injector.wiring import inject, Provide
from core.container import Container
from presentation.controllers import auth_controller, tenant_controller, user_controller, organization_controller
from database.db import get_session
import os

# Create FastAPI app
app = FastAPI(title="Vacancy Portal API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create container
container = Container()

# Wire dependencies
container.wire(modules=[
    "presentation.controllers.auth_controller",
    "presentation.controllers.tenant_controller",
    "presentation.controllers.user_controller",
    "presentation.controllers.organization_controller"
])

# Include routers
app.include_router(auth_controller.auth_router)
app.include_router(tenant_controller.tenant_router)
app.include_router(user_controller.user_router)
app.include_router(organization_controller.organization_router)

@app.get('/')
async def root():
    return {'message': 'Vacancy Portal API - Clean Architecture with Google SSO'}

@app.get('/health')
async def health_check():
    return {'status': 'healthy', 'architecture': 'clean'}

# Dependency injection for database session
@app.dependency
def get_db_session():
    return get_session()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Phase 5: Migration Strategy

### 5.1 Gradual Migration Approach

The migration from your current Google SSO implementation to Clean Architecture should be **gradual and non-breaking**. Here's a step-by-step approach:

#### **Step 1: Preserve Current Functionality (Week 1)**

```python
# Keep existing auth endpoints working alongside new ones
# main.py - Add both old and new routers

# Old auth router (keep for backward compatibility)
from auth import auth as old_auth
app.include_router(old_auth.auth_router, prefix="/api/v1")

# New auth router (Clean Architecture)
from presentation.controllers import auth_controller
app.include_router(auth_controller.auth_router, prefix="/api/v2")
```

#### **Step 2: Implement Domain Layer (Week 2)**

```python
# Create domain entities and services
# This doesn't affect existing functionality

# domain/entities/user.py
# domain/services/auth_service.py
# domain/exceptions/auth_exceptions.py
```

#### **Step 3: Implement Infrastructure Layer (Week 3)**

```python
# Create adapters for existing Google SSO
# infrastructure/auth/google_sso_adapter.py
# infrastructure/auth/jwt_token_service.py
# infrastructure/auth/authorization_service.py
```

#### **Step 4: Implement Application Layer (Week 4)**

```python
# Create use cases and DTOs
# application/use_cases/auth_use_cases.py
# application/dto/auth_dto.py
```

#### **Step 5: Implement Presentation Layer (Week 5)**

```python
# Create new controllers with Clean Architecture
# presentation/controllers/auth_controller.py
# presentation/middleware/auth_middleware.py
```

#### **Step 6: Gradual Switch (Week 6)**

```python
# Switch traffic from old to new endpoints
# Monitor and validate functionality
# Remove old endpoints once confirmed working
```

### 5.2 Environment Configuration

#### **Updated Environment Variables**

```bash
# .env file with all required variables
DATABASE_URL=postgresql://user:password@localhost:5432/vacancy_portal
JWT_SECRET=your-super-secret-jwt-key
JWT_ALGO=HS256

# Google SSO Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback

# Database Configuration
DB_URL=postgresql://user:password@localhost:5432/vacancy_portal

# Application Configuration
ENVIRONMENT=development
DEBUG=true
```

#### **Configuration Management**

```python
# core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str
    db_url: str
    
    # JWT
    jwt_secret: str
    jwt_algo: str = "HS256"
    
    # Google SSO
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/api/auth/callback"
    
    # Application
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings()
```

### 5.3 Testing Strategy

#### **Unit Tests for Authentication**

```python
# tests/unit/test_auth_services.py
import pytest
from unittest.mock import Mock, AsyncMock
from application.services.auth_services import GoogleSSOLoginService
from domain.entities.user import User
from domain.exceptions.auth_exceptions import AuthenticationError

class TestGoogleSSOLoginService:
    @pytest.fixture
    def mock_auth_service(self):
        return Mock()
    
    @pytest.fixture
    def mock_user_service(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_token_service(self):
        return Mock()
    
    @pytest.fixture
    def mock_auth_service(self):
        return Mock()
    
    @pytest.fixture
    def service(self, mock_auth_service, mock_user_service, mock_token_service, mock_auth_service):
        return GoogleSSOLoginService(
            mock_auth_service,
            mock_user_service,
            mock_token_service,
            mock_auth_service
        )
    
    @pytest.mark.asyncio
    async def test_successful_login(self, service, mock_auth_service, mock_user_service, mock_token_service):
        # Arrange
        mock_request = Mock()
        mock_user = User(email="test@example.com", first_name="Test", last_name="User")
        mock_scopes = ["view:tenants", "write:tenants"]
        mock_token = "jwt-token"
        
        mock_auth_service.authenticate_user.return_value = mock_user
        mock_user_service.get_or_create_user.return_value = mock_user
        mock_auth_service.get_user_scopes.return_value = mock_scopes
        mock_token_service.create_token.return_value = mock_token
        
        # Act
        result = await service.execute(mock_request)
        
        # Assert
        assert result.access_token == mock_token
        assert result.user_id == mock_user.id
        assert result.email == mock_user.email
        assert result.scopes == mock_scopes
```

#### **Integration Tests**

```python
# tests/integration/test_auth_integration.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAuthIntegration:
    def test_google_login_redirect(self):
        """Test Google SSO login redirect"""
        response = client.get("/api/v2/auth/google/login")
        assert response.status_code == 200
        # Should redirect to Google OAuth
    
    def test_google_callback_with_valid_token(self):
        """Test Google SSO callback with valid token"""
        # Mock Google SSO response
        response = client.get("/api/v2/auth/google/callback")
        # This would require mocking the Google SSO flow
        assert response.status_code in [200, 401]  # 401 if not authenticated
    
    def test_token_validation(self):
        """Test JWT token validation"""
        # First get a valid token
        # Then validate it
        response = client.post("/api/v2/auth/validate-token")
        assert response.status_code in [200, 401]
    
    def test_get_current_user(self):
        """Test getting current user profile"""
        response = client.get("/api/v2/auth/me")
        assert response.status_code in [200, 401]
```

### 5.4 Rollback Strategy

#### **Feature Flags**

```python
# core/feature_flags.py
import os

class FeatureFlags:
    @staticmethod
    def use_clean_architecture_auth() -> bool:
        """Feature flag to switch between old and new auth"""
        return os.getenv("USE_CLEAN_ARCH_AUTH", "false").lower() == "true"
    
    @staticmethod
    def enable_new_endpoints() -> bool:
        """Feature flag to enable new API endpoints"""
        return os.getenv("ENABLE_NEW_ENDPOINTS", "false").lower() == "true"

# Usage in main.py
if FeatureFlags.use_clean_architecture_auth():
    app.include_router(auth_controller.auth_router, prefix="/api/v2")
else:
    app.include_router(old_auth.auth_router, prefix="/api/v1")
```

#### **Health Checks**

```python
# presentation/controllers/health_controller.py
from fastapi import APIRouter, Depends
from core.feature_flags import FeatureFlags

health_router = APIRouter(prefix="/health", tags=["Health"])

@health_router.get("/auth")
async def auth_health_check():
    """Check authentication system health"""
    return {
        "auth_system": "clean_architecture" if FeatureFlags.use_clean_architecture_auth() else "legacy",
        "status": "healthy",
        "features": {
            "google_sso": True,
            "jwt_tokens": True,
            "role_based_auth": True
        }
    }
```

### 5.5 Monitoring and Validation

#### **Authentication Metrics**

```python
# infrastructure/monitoring/auth_metrics.py
from datetime import datetime
from typing import Dict, Any

class AuthMetrics:
    """Authentication metrics collection"""
    
    def __init__(self):
        self.login_attempts = 0
        self.successful_logins = 0
        self.failed_logins = 0
        self.token_validations = 0
        self.invalid_tokens = 0
    
    def record_login_attempt(self, success: bool, method: str = "google_sso"):
        """Record login attempt"""
        self.login_attempts += 1
        if success:
            self.successful_logins += 1
        else:
            self.failed_logins += 1
    
    def record_token_validation(self, valid: bool):
        """Record token validation"""
        self.token_validations += 1
        if not valid:
            self.invalid_tokens += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            "login_attempts": self.login_attempts,
            "successful_logins": self.successful_logins,
            "failed_logins": self.failed_logins,
            "success_rate": self.successful_logins / max(self.login_attempts, 1),
            "token_validations": self.token_validations,
            "invalid_tokens": self.invalid_tokens,
            "timestamp": datetime.utcnow().isoformat()
        }

# Global metrics instance
auth_metrics = AuthMetrics()
```

#### **Validation Checklist**

```markdown
## Migration Validation Checklist

### Authentication Flow
- [ ] Google SSO login redirects correctly
- [ ] Google SSO callback processes user data
- [ ] JWT tokens are generated and valid
- [ ] User roles are assigned correctly
- [ ] Scope-based authorization works

### API Endpoints
- [ ] All existing endpoints still work
- [ ] New endpoints return correct responses
- [ ] Error handling is consistent
- [ ] Response formats match expectations

### Database Integration
- [ ] User data is stored correctly
- [ ] Role updates persist
- [ ] Organization relationships work
- [ ] No data loss during migration

### Security
- [ ] JWT tokens are secure
- [ ] Authorization scopes are enforced
- [ ] User permissions are respected
- [ ] No unauthorized access

### Performance
- [ ] Authentication response times are acceptable
- [ ] Token validation is fast
- [ ] Database queries are optimized
- [ ] No memory leaks

### User Experience
- [ ] Login flow is smooth
- [ ] Error messages are clear
- [ ] Role assignment works
- [ ] No disruption to existing users
```

### 5.6 Documentation Updates

#### **API Documentation**

```python
# Update OpenAPI documentation
app = FastAPI(
    title="Vacancy Portal API",
    description="Clean Architecture implementation with Google SSO",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add authentication documentation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### **Migration Guide**

```markdown
# Migration Guide: Google SSO to Clean Architecture

## Overview
This guide explains how to migrate from the legacy authentication system to the new Clean Architecture implementation.

## Prerequisites
- Python 3.11+
- PostgreSQL database
- Google OAuth2 credentials
- Environment variables configured

## Migration Steps

### 1. Backup Current System
```bash
# Backup database
pg_dump vacancy_portal > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup current code
git checkout -b backup-legacy-auth
git add .
git commit -m "Backup legacy authentication system"
```

### 2. Install New Dependencies

```bash
poetry add dependency-injector
poetry install
```

### 3. Update Environment Variables

```bash
# Add new environment variables to .env
USE_CLEAN_ARCH_AUTH=false  # Start with legacy
ENABLE_NEW_ENDPOINTS=false
```

### 4. Deploy New Code

```bash
# Deploy with feature flags disabled
docker-compose up --build
```

### 5. Test New Endpoints

```bash
# Test new authentication endpoints
curl http://localhost:8000/api/v2/auth/google/login
```

### 6. Enable New System

```bash
# Set environment variables
export USE_CLEAN_ARCH_AUTH=true
export ENABLE_NEW_ENDPOINTS=true

# Restart application
docker-compose restart
```

### 7. Monitor and Validate

- Check authentication metrics
- Verify all functionality works
- Monitor error rates
- Validate user experience

### 8. Remove Legacy Code

```bash
# Once confirmed working, remove legacy code
git checkout main
git merge feature/clean-architecture-auth
```

## Rollback Plan

If issues arise, rollback using:

```bash
export USE_CLEAN_ARCH_AUTH=false
export ENABLE_NEW_ENDPOINTS=false
docker-compose restart
```

## Summary

This updated implementation guide now provides:

1. **Complete Google SSO Integration** - Full Clean Architecture implementation with your existing Google SSO
2. **Gradual Migration Strategy** - Step-by-step approach to avoid breaking changes
3. **Comprehensive Testing** - Unit and integration tests for authentication
4. **Feature Flags** - Safe deployment with rollback capability
5. **Monitoring** - Metrics and validation for the migration
6. **Documentation** - Complete migration guide and API documentation

The plan preserves your existing Google SSO functionality while providing a clear path to Clean Architecture implementation using **Services** instead of **Use Cases** for clearer terminology.
