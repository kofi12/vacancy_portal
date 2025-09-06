from typing import List
from domain.entities.base_entity import BaseEntity
from datetime import datetime
from dataclasses import dataclass

from domain.entities.tenant_entity import TenantEntity

@dataclass
class OrganizationEntity(BaseEntity):
    """Organization Entity"""
    _business_name: str
    _address: str
    _number_of_beds: int
    _owner_id: int
    _tenants: List[TenantEntity]

    def __init__(self, id: int | None, created_at: datetime,
                 business_name: str, address: str, number_of_beds: int,
                 owner_id: int):
        super().__init__(id, created_at)
        # Use setters to ensure validation during initialization
        self._business_name = business_name
        self._address = address
        self._number_of_beds = number_of_beds
        self._owner_id = owner_id

    def has_beds(self) -> bool:
        if self._number_of_beds - len(self._tenants) > 0:
            return True
        else:
            return False

    def number_of_vacancies(self) -> int:
        return self._number_of_beds - len(self._tenants)


    @classmethod
    def create_org(cls, business_name: str, address: str,
                    number_of_beds: int, owner_id: int) -> 'OrganizationEntity':
        """Factory method for creating new organizations with some validation"""
        if not business_name:
            raise ValueError("Missing business name")
        if not address:
            raise ValueError("Missing address")
        if not number_of_beds:
            raise ValueError("Missing number of beds")

        return cls(None,
                   datetime.now(),
                   business_name,
                   address,
                   number_of_beds,
                   owner_id
        )

