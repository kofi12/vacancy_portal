from abc import ABC, abstractmethod
from ..entities.org_entity import OrganizationEntity

class OrganizationRepository(ABC):
    """Repository interface for organization data I/O"""

@abstractmethod
async def create(self, org: OrganizationEntity) -> OrganizationEntity: # type: ignore
    """Create a new organization"""
    pass

@abstractmethod
async def update(self, org: OrganizationEntity):
    """Update a organization"""
    pass

@abstractmethod
async def delete(self, org_id: int):
    """Delete a organization"""
    pass

@abstractmethod
async def get_by_id(self, org_id: int) -> OrganizationEntity: # type: ignore
    """Get a organization by ID"""
    pass

@abstractmethod
async def get_org_by_name(self, name: str) -> OrganizationEntity: #type: ignore
    """Get a organization by name"""
    pass

@abstractmethod
async def exists(self, org: OrganizationEntity) -> bool: #type: ignore
    """Check if a Organization exists"""
    pass