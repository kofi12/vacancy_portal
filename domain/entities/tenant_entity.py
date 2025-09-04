from datetime import datetime
from domain.entities.base_entity import BaseEntity
from dataclasses import dataclass

@dataclass
class TenantEntity(BaseEntity):
    """Tenant domain entity with business logic"""

    _name: str
    _admission_date: datetime | None
    _organization_id: int
    _is_waitlist: bool = True

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
                      organization_id: int):
        """Factory method for creating new tenants with validation"""
        if not name or not name.strip():
            raise ValueError("Tenant name cannot be empty")
        if not organization_id:
            raise ValueError("Valid organization ID required")

        return cls(_name=name,
                   _admission_date=None,
                   _organization_id=organization_id,
                   _is_waitlist=True
        )