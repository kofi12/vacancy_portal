from dataclasses import dataclass

@dataclass
class OrganizationDomain:
    """Internal Organization Representation"""
    id: int | None
    business_name: str
    address: str
    number_of_beds: int | None
    owner_id: int

    #Business Rules

    pass
