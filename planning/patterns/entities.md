# 🏗️ Domain Entities Pattern

## Overview

Domain entities represent core business concepts with identity and behavior. They encapsulate business logic and enforce business rules.

## Key Characteristics

### ✅ What Entities Should Have

- **Identity** - Unique identifier (ID)
- **Business Logic** - Methods that express business rules
- **Lifecycle** - Creation, updates, validation
- **Immutability** - Where appropriate for business rules

### ❌ What Entities Should NOT Have

- Database concerns (SQL, connections)
- HTTP concerns (requests, responses)
- External service calls
- UI/formatting logic

## Implementation Patterns

### Basic Entity Structure

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class BaseEntity:
    """Base class for all domain entities"""
    
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class TenantEntity(BaseEntity):
    """Tenant domain entity with admission logic"""
    
    name: str
    admission_date: Optional[datetime] = None
    is_waitlist: bool = False
    organization_id: int
    
    def can_be_admitted(self) -> bool:
        """Business rule: tenant admission eligibility"""
        return self.is_waitlist and self.admission_date is None
    
    def admit(self, admission_date: datetime) -> None:
        """Business rule: admit tenant"""
        if not self.can_be_admitted():
            raise ValueError("Tenant cannot be admitted")
        self.admission_date = admission_date
        self.is_waitlist = False
    
    @classmethod
    def create_tenant(cls, name: str, organization_id: int) -> 'TenantEntity':
        """Factory method with validation"""
        if not name or not name.strip():
            raise ValueError("Tenant name cannot be empty")
        return cls(name=name.strip(), organization_id=organization_id)
```

### Entity Lifecycle Pattern

```python
@dataclass
class UserEntity(BaseEntity):
    email: str
    role: str = "pending"
    
    def activate(self) -> None:
        """Transition from pending to active"""
        if self.role != "pending":
            raise ValueError("Only pending users can be activated")
        self.role = "active"
    
    def promote_to_admin(self) -> None:
        """Business rule: role promotion"""
        if self.role not in ["active", "owner"]:
            raise ValueError("Insufficient permissions for admin role")
        self.role = "admin"
    
    def is_active(self) -> bool:
        """Business rule: active status"""
        return self.role in ["active", "owner", "admin"]
```

## Common Patterns

### Factory Method Pattern

```python
@dataclass
class OrganizationEntity(BaseEntity):
    business_name: str
    address: str
    max_capacity: int
    
    @classmethod
    def create_organization(cls, business_name: str, address: str, 
                          max_capacity: int) -> 'OrganizationEntity':
        """Factory with comprehensive validation"""
        if not business_name or len(business_name.strip()) < 2:
            raise ValueError("Business name must be at least 2 characters")
        if not address or len(address.strip()) < 10:
            raise ValueError("Address must be at least 10 characters")
        if max_capacity <= 0:
            raise ValueError("Max capacity must be positive")
        
        return cls(
            business_name=business_name.strip(),
            address=address.strip(),
            max_capacity=max_capacity
        )
```

### Entity Relationship Pattern

```python
@dataclass
class OrganizationEntity(BaseEntity):
    business_name: str
    tenant_ids: List[int] = field(default_factory=list)
    
    def add_tenant(self, tenant_id: int) -> None:
        """Business rule: add tenant to organization"""
        if tenant_id in self.tenant_ids:
            raise ValueError("Tenant already belongs to organization")
        if len(self.tenant_ids) >= self.max_capacity:
            raise ValueError("Organization at maximum capacity")
        self.tenant_ids.append(tenant_id)
    
    def remove_tenant(self, tenant_id: int) -> None:
        """Business rule: remove tenant from organization"""
        if tenant_id not in self.tenant_ids:
            raise ValueError("Tenant does not belong to organization")
        self.tenant_ids.remove(tenant_id)
    
    def get_capacity_utilization(self) -> float:
        """Business rule: calculate capacity usage"""
        return len(self.tenant_ids) / self.max_capacity
```

## Testing Patterns

### Unit Test Pattern

```python
def test_tenant_admission():
    # Arrange
    tenant = TenantEntity.create_tenant("John Doe", 1, is_waitlist=True)
    
    # Act
    tenant.admit(datetime.utcnow())
    
    # Assert
    assert tenant.is_waitlist == False
    assert tenant.admission_date is not None

def test_tenant_admission_invalid_state():
    # Arrange
    tenant = TenantEntity.create_tenant("Jane Doe", 1, is_waitlist=False)
    
    # Act & Assert
    with pytest.raises(ValueError, match="Tenant cannot be admitted"):
        tenant.admit(datetime.utcnow())
```

### Business Rule Test Pattern

```python
def test_organization_capacity_validation():
    # Arrange
    org = OrganizationEntity.create_organization("Test Org", "123 Main St", 5)
    
    # Act: Fill to capacity
    for i in range(5):
        org.add_tenant(i + 1)
    
    # Assert: At capacity
    assert org.get_capacity_utilization() == 1.0
    
    # Act & Assert: Try to exceed capacity
    with pytest.raises(ValueError, match="Organization at maximum capacity"):
        org.add_tenant(6)
```

## Best Practices

### 1. **Keep Entities Focused**

```python
# ✅ Good: Single responsibility
class TenantEntity(BaseEntity):
    def admit(self): pass
    def discharge(self): pass

# ❌ Bad: Multiple responsibilities
class TenantEntity(BaseEntity):
    def admit(self): pass
    def save_to_database(self): pass  # Infrastructure concern
    def send_email(self): pass        # External service concern
```

### 2. **Use Value Objects for Complex Types**

```python
@dataclass(frozen=True)
class EmailAddress:
    value: str
    
    def __post_init__(self):
        # Validation logic here
        pass

@dataclass
class UserEntity(BaseEntity):
    email: EmailAddress  # Use value object instead of string
```

### 3. **Prefer Explicit Business Methods**

```python
# ✅ Good: Explicit business intent
class TenantEntity(BaseEntity):
    def admit(self, admission_date: datetime): pass
    def discharge(self, discharge_date: datetime): pass

# ❌ Bad: Generic setter
class TenantEntity(BaseEntity):
    def update_status(self, status: str, date: datetime): pass
```

### 4. **Fail Fast with Validation**

```python
class TenantEntity(BaseEntity):
    def __post_init__(self):
        # Validate immediately after creation
        if not self.name:
            raise ValueError("Tenant name is required")
```

## Common Pitfalls

### 1. **Anemic Domain Model**

```python
# ❌ Bad: Just data, no behavior
@dataclass
class TenantEntity(BaseEntity):
    name: str
    admitted: bool = False
    # No business methods!

# ✅ Good: Rich domain model
@dataclass
class TenantEntity(BaseEntity):
    name: str
    admission_date: Optional[datetime] = None
    
    def admit(self, date: datetime): pass
    def is_admitted(self) -> bool: pass
```

### 2. **Infrastructure Concerns in Entities**

```python
# ❌ Bad: Database logic in entity
class TenantEntity(BaseEntity):
    def save(self, db_session): pass  # Infrastructure concern

# ✅ Good: Pure business logic
class TenantEntity(BaseEntity):
    def validate_for_save(self): pass  # Business validation
```

### 3. **Primitive Obsession**

```python
# ❌ Bad: Using primitives for complex concepts
@dataclass
class UserEntity(BaseEntity):
    email: str  # Just a string
    phone: str  # Just a string

# ✅ Good: Use value objects
@dataclass
class UserEntity(BaseEntity):
    email: EmailAddress
    phone: PhoneNumber
```

## Migration Guide

### From Anemic to Rich Entities

```python
# Before: Anemic entity
@dataclass
class Tenant:
    name: str
    admitted: bool = False

# After: Rich entity
@dataclass
class TenantEntity(BaseEntity):
    name: str
    admission_date: Optional[datetime] = None
    
    def admit(self, date: datetime):
        if self.admission_date:
            raise ValueError("Already admitted")
        self.admission_date = date
    
    def is_admitted(self) -> bool:
        return self.admission_date is not None
```

This pattern ensures your domain entities are the heart of your business logic, making your application more maintainable and testable.
