from datetime import datetime
from domain.entities.base_entity import BaseEntity
from dataclasses import dataclass

@dataclass
class TenantEntity(BaseEntity):
    """Tenant domain entity with business logic"""

    def __init__(self, name: str, organization_id: int, admission_date: datetime | None = None):
        # Call parent constructor
        super().__init__(None, datetime.now())

        # Set attributes
        self._name = name
        self._admission_date = admission_date
        self._organization_id = organization_id
        self._is_waitlist = True

    def admittable(self) -> bool:
        """Business rule: only tenants on a waitlist can be admitted"""
        return self._is_waitlist

    def admit(self):
        """Business logic: admit the tenant only if they are admittable"""
        if not self.admittable():
            raise ValueError("Tenant is not on a waitlist and therefore cannot be admitted")
        self._admission_date = datetime.now()
        self._is_waitlist = False

    @classmethod
    def create_tenant(cls,
                      name: str,
                      organization_id: int) -> "TenantEntity":
        """Factory method for creating new tenants with validation"""
        if not name or not name.strip():
            raise ValueError("Tenant name cannot be empty")
        if not organization_id:
            raise ValueError("Valid organization ID required")

        return cls(name=name,
                   organization_id=organization_id,
                   admission_date=None
        )