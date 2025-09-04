from typing import List
from domain.entities.base_entity import BaseEntity
from datetime import datetime

class OrganizationEntity(BaseEntity):
    """Organization Entity"""
    _business_name: str
    _address: str
    _number_of_beds: int
    _owner_id: int

    def __init__(self, id: int | None, created_at:datetime,
                 business_name: str, address: str, number_of_beds: int,
                 owner_id: int):
        super().__init__(id, created_at)
        # Use setters to ensure validation during initialization
        self.business_name = business_name
        self.address = address
        self.number_of_beds = number_of_beds
        self.owner_id = owner_id

    @property
    def business_name(self) -> str:
        if not self._business_name:
            raise ValueError("Business name doesn't exist")
        return self._business_name

    @business_name.setter
    def business_name(self, value : str):
        if not value or value.strip() == "":
            raise ValueError("Business name cannot be empty")
        self._business_name = value

    @property
    def address(self) -> str:
        if not self._address:
            raise ValueError("Address doesn't exist")
        return self._address

    @address.setter
    def address(self, value : str):
        if not value or value.strip() == "":
            raise ValueError("Address cannot be empty")
        self._address = value

    @property
    def number_of_beds(self) -> int:
        if not self._number_of_beds:
            raise ValueError("Number of beds undetermined")
        return self._number_of_beds

    @number_of_beds.setter
    def number_of_beds(self, value : int):
        if value <= 0:
            raise ValueError("Number of beds must be greater than 0")
        self._number_of_beds = value

    @property
    def owner_id(self) -> int:
        if not self._owner_id:
            raise ValueError("Organization does not have an owner")
        return self._owner_id

    @owner_id.setter
    def owner_id(self, value : int):
        if not value or value == 0:
            raise ValueError("Owner id must be a none zero number")
        self._owner_id = value

    def get_tenant_count(self, tenant_list: List) -> int:
        """Return the number of tenants in the organization"""
        # assume list of tenants belongs to this specific organization
        return len(tenant_list)

    def number_of_beds_available(self, tenant_list: List) -> int:
        """Return the number of beds available"""
        current_number_of_tenants = self.get_tenant_count(tenant_list)
        return self._number_of_beds - current_number_of_tenants

    def has_available_beds(self, tenant_list: List) -> bool:
        """Check if beds are available"""
        if tenant_list:
            return self.number_of_beds_available(tenant_list) > 0
        else:
            raise ValueError("Tenant list is empty or null")

    def can_admit_tenant(self, tenant_list: List) -> bool:
        """"Checks if tenant can be admitted"""
        try:
            return self.has_available_beds(tenant_list)
        except:
            raise ValueError("Cannot admit tenant, at capacity")

    def validate_organization(self) -> bool:
        """Validate organization data according to business rules"""

        if not self:
            raise ValueError("No Org exists")
        return (
            len(self._business_name.strip()) > 0 and
            len(self._address.strip()) > 0 and
            self._number_of_beds > 0
        )

    @classmethod
    def create_org(cls, business_name: str, address: str,
                    number_of_beds: int, owner_id: int) -> 'OrganizationEntity':
        return cls(None, datetime.now(), business_name,
                   address, number_of_beds, owner_id)

