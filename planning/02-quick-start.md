# ⚡ Quick Start: Your First Domain Entity (30 minutes)

This guide will get you implementing Clean Architecture immediately using your existing codebase.

## 🎯 What You'll Accomplish

- ✅ Create your first domain entity
- ✅ Write unit tests for business logic
- ✅ See the difference between current and clean approaches
- ✅ Have working code that doesn't break existing functionality

## 📋 Prerequisites

- [x] Python environment set up
- [x] Current codebase working
- [x] 30 minutes of focused time

## 🛠️ Step-by-Step Implementation

### Step 1: Create Base Entity (5 minutes)

**Create file:** `domain/entities/base_entity.py`

```python
from abc import ABC
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

### Step 2: Refactor Tenant Entity (10 minutes)

**Update file:** `domain/entities/tenant_entity.py`

Replace the current content with this clean architecture version:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from domain.entities.base_entity import BaseEntity

@dataclass
class TenantEntity(BaseEntity):
    """Tenant domain entity with admission management logic"""
    
    name: str
    admission_date: Optional[datetime] = None
    discharge_date: Optional[datetime] = None
    is_waitlist: bool = False
    organization_id: int
    
    def can_be_admitted(self) -> bool:
        """Business rule: Check if tenant can be admitted"""
        return self.is_waitlist and self.admission_date is None
    
    def admit(self, admission_date: datetime) -> None:
        """Business logic: Admit the tenant"""
        if not self.can_be_admitted():
            raise ValueError("Tenant cannot be admitted")
        self.admission_date = admission_date
        self.is_waitlist = False
    
    def is_currently_admitted(self) -> bool:
        """Business rule: Check if tenant is currently admitted"""
        return (self.admission_date is not None and 
                self.discharge_date is None)
    
    def can_be_discharged(self) -> bool:
        """Business rule: Check if tenant can be discharged"""
        return self.admission_date is not None and self.discharge_date is None
    
    def discharge(self, discharge_date: datetime) -> None:
        """Business logic: Discharge the tenant"""
        if not self.can_be_discharged():
            raise ValueError("Tenant cannot be discharged")
        self.discharge_date = discharge_date

    @classmethod
    def create_tenant(cls, name: str, organization_id: int, is_waitlist: bool = False) -> 'TenantEntity':
        """Factory method for creating new tenants with validation"""
        if not name or not name.strip():
            raise ValueError("Tenant name cannot be empty")
        if organization_id <= 0:
            raise ValueError("Valid organization ID required")
        
        return cls(
            id=None,
            created_at=datetime.utcnow(),
            name=name.strip(),
            organization_id=organization_id,
            is_waitlist=is_waitlist
        )
```

### Step 3: Write Unit Tests (10 minutes)

**Create file:** `tests/domain/test_tenant_entity.py`

```python
import pytest
from datetime import datetime, timedelta
from domain.entities.tenant_entity import TenantEntity

class TestTenantEntity:
    
    def test_create_tenant_success(self):
        """Test successful tenant creation"""
        tenant = TenantEntity.create_tenant(
            name="John Doe",
            organization_id=1,
            is_waitlist=True
        )
        
        assert tenant.name == "John Doe"
        assert tenant.organization_id == 1
        assert tenant.is_waitlist == True
        assert tenant.admission_date is None
    
    def test_create_tenant_empty_name_raises_error(self):
        """Test that empty name raises ValueError"""
        with pytest.raises(ValueError, match="Tenant name cannot be empty"):
            TenantEntity.create_tenant("", organization_id=1)
    
    def test_create_tenant_invalid_org_id_raises_error(self):
        """Test that invalid organization ID raises ValueError"""
        with pytest.raises(ValueError, match="Valid organization ID required"):
            TenantEntity.create_tenant("John Doe", organization_id=0)
    
    def test_can_be_admitted_waitlist_tenant(self):
        """Test admission eligibility for waitlist tenant"""
        tenant = TenantEntity.create_tenant("Jane Doe", 1, is_waitlist=True)
        assert tenant.can_be_admitted() == True
    
    def test_can_be_admitted_already_admitted_tenant(self):
        """Test admission eligibility for already admitted tenant"""
        tenant = TenantEntity.create_tenant("Jane Doe", 1, is_waitlist=False)
        tenant.admission_date = datetime.utcnow()
        
        assert tenant.can_be_admitted() == False
    
    def test_admit_tenant_success(self):
        """Test successful tenant admission"""
        admission_date = datetime.utcnow()
        tenant = TenantEntity.create_tenant("Jane Doe", 1, is_waitlist=True)
        
        tenant.admit(admission_date)
        
        assert tenant.admission_date == admission_date
        assert tenant.is_waitlist == False
        assert tenant.is_currently_admitted() == True
    
    def test_admit_already_admitted_tenant_raises_error(self):
        """Test that admitting already admitted tenant raises error"""
        tenant = TenantEntity.create_tenant("Jane Doe", 1, is_waitlist=False)
        tenant.admission_date = datetime.utcnow()
        
        with pytest.raises(ValueError, match="Tenant cannot be admitted"):
            tenant.admit(datetime.utcnow())
    
    def test_discharge_tenant_success(self):
        """Test successful tenant discharge"""
        admission_date = datetime.utcnow()
        discharge_date = admission_date + timedelta(days=30)
        
        tenant = TenantEntity.create_tenant("Jane Doe", 1, is_waitlist=True)
        tenant.admit(admission_date)
        
        tenant.discharge(discharge_date)
        
        assert tenant.discharge_date == discharge_date
        assert tenant.is_currently_admitted() == False
    
    def test_discharge_not_admitted_tenant_raises_error(self):
        """Test that discharging non-admitted tenant raises error"""
        tenant = TenantEntity.create_tenant("Jane Doe", 1, is_waitlist=True)
        
        with pytest.raises(ValueError, match="Tenant cannot be discharged"):
            tenant.discharge(datetime.utcnow())
    
    def test_is_currently_admitted_admitted_tenant(self):
        """Test current admission status for admitted tenant"""
        tenant = TenantEntity.create_tenant("Jane Doe", 1, is_waitlist=True)
        admission_date = datetime.utcnow()
        tenant.admit(admission_date)
        
        assert tenant.is_currently_admitted() == True
    
    def test_is_currently_admitted_discharged_tenant(self):
        """Test current admission status for discharged tenant"""
        tenant = TenantEntity.create_tenant("Jane Doe", 1, is_waitlist=True)
        admission_date = datetime.utcnow()
        discharge_date = admission_date + timedelta(days=30)
        
        tenant.admit(admission_date)
        tenant.discharge(discharge_date)
        
        assert tenant.is_currently_admitted() == False
```

### Step 4: Run Tests (5 minutes)

```bash
# Install pytest if you haven't already
pip install pytest

# Make sure you're in the project root directory
cd /Users/aaronkofihaizel/aaronDev/vacancy_portal

# Create tests directory if it doesn't exist
mkdir -p tests/domain

# Run the tests
pytest tests/domain/test_tenant_entity.py -v
```

You should see output like:

============================= test session starts ==============================
tests/domain/test_tenant_entity.py::TestTenantEntity::test_create_tenant_success PASSED
tests/domain/test_tenant_entity.py::TestTenantEntity::test_create_tenant_empty_name_raises_error PASSED
tests/domain/test_tenant_entity.py::TestTenantEntity::test_create_tenant_invalid_org_id_raises_error PASSED
tests/domain/test_tenant_entity.py::TestTenantEntity::test_can_be_admitted_waitlist_tenant PASSED
tests/domain/test_tenant_entity.py::TestTenantEntity::test_can_be_admitted_already_admitted_tenant PASSED
tests/domain/test_tenant_entity.py::TestTenantEntity::test_admit_tenant_success PASSED
tests/domain/test_tenant_entity.py::TestTenantEntity::test_admit_already_admitted_tenant_raises_error PASSED
tests/domain/test_tenant_entity.py::TestTenantEntity::test_discharge_tenant_success PASSED
tests/domain/test_tenant_entity.py::TestTenantEntity::test_discharge_not_admitted_tenant_raises_error PASSED
tests/domain/test_tenant_entity.py::TestTenantEntity::test_is_currently_admitted_admitted_tenant PASSED
tests/domain/test_tenant_entity.py::TestTenantEntity::test_is_currently_admitted_discharged_tenant PASSED
============================== 11 passed in 0.12s ==============================

## ✅ Success Check

If all tests pass, congratulations! You've successfully:

1. ✅ Created a domain entity with business logic
2. ✅ Moved validation logic from controllers/DAOs to the domain
3. ✅ Made business rules explicit and testable
4. ✅ Created code that's independent of your web framework
5. ✅ Written comprehensive unit tests

## 🔄 Integration with Existing Code

Your domain layer works alongside your existing code without breaking it. Here's how to integrate:

### Option 1: Gradual Migration (Recommended)

Keep your existing controllers working while you build the new architecture.

### Option 2: Parallel Implementation

Create new endpoints with clean architecture while maintaining old ones.

## 🆘 Need Help?

### Tests Failing?

**Issue: Import errors*

ModuleNotFoundError: No module named 'domain'

**Solution:** Add your project root to Python path:

```python
# In your test file or at the top of your test session
import sys
sys.path.append('/Users/aaronkofihaizel/aaronDev/vacancy_portal')
```

**Issue: Business logic not working as expected*

- Compare your entity methods with the examples above line by line
- Check that your dataclass fields match exactly
- Verify your validation logic

**Issue: Test discovery issues*

```bash
# Try running with explicit path
pytest tests/domain/test_tenant_entity.py --tb=short

# Or run all tests in the domain directory
pytest tests/domain/ -v
```

### Common Mistakes

1. **Wrong file paths**: Make sure the domain package is importable
2. **Missing dependencies**: Ensure you have all required packages installed
3. **Syntax errors**: Double-check your dataclass and method definitions
4. **Test setup**: Make sure pytest is properly configured

## 📚 What You've Learned

### Before (Current Approach)

```python
# Business logic mixed in controller/DAO
def tenant_create(user_data: TenantBase, db: Session):
    if not tenant_exists(user_data, db):  # Business logic in DAO
        tenant = Tenant(**user_data_dict)
        db.add(tenant)
        return tenant
```

### After (Clean Architecture)

```python
# Business logic in domain entity
@dataclass
class TenantEntity(BaseEntity):
    name: str
    is_waitlist: bool = False
    
    def can_be_admitted(self) -> bool:
        return self.is_waitlist  # Business rule explicit and testable
```

## 🔄 Next Steps

Now that you have a working domain entity, you can:

1. **Continue with Repository Interfaces**: Create contracts for data access
2. **Build Domain Services**: Add business logic that spans multiple entities
3. **Read the [Domain Layer Phase Guide](phases/01-domain-layer.md)** for the complete implementation
4. **Explore [Patterns](patterns/)** for detailed implementation examples

## 🎯 Key Takeaways

- **Domain entities** contain business logic and rules
- **Business rules are explicit** and easily testable
- **Framework independence** means your business logic can survive technology changes
- **Small, focused methods** make code easier to understand and maintain
- **Comprehensive tests** ensure your business logic works correctly

## 🏆 Achievement Unlocked

You've just implemented your first piece of Clean Architecture! This domain entity:

- ✅ Contains business rules that would otherwise be scattered
- ✅ Is completely independent of your web framework
- ✅ Can be tested without database or network dependencies
- ✅ Makes business logic explicit and easy to understand
- ✅ Follows domain-driven design principles

---

**🎉 Excellent work!** You've taken your first concrete step toward Clean Architecture.

**Ready for more?** → [Domain Layer Phase Guide](phases/01-domain-layer.md)

## What This Document Provides

This Quick Start guide gives developers:

1. **Immediate action** - Start implementing in 30 minutes
2. **Concrete examples** - Real code they can copy and modify
3. **Before/after comparisons** - Clear understanding of the benefits
4. **Comprehensive testing** - Shows how to test the new architecture
5. **Troubleshooting guidance** - Common issues and solutions
6. **Integration advice** - How to work alongside existing code

The guide is designed to be:

- ✅ **Practical** - Real code that works with their existing codebase
- ✅ **Progressive** - Builds skills incrementally
- ✅ **Motivational** - Shows immediate benefits
- ✅ **Supportive** - Includes troubleshooting and next steps
