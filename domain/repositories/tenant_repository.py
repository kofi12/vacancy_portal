from abc import ABC, abstractmethod
from typing import List
from domain.entities.tenant_entity import TenantEntity

class TenantRepository(ABC):
    """Repository interface for tenant data access"""

@abstractmethod
async def create(self, tenant: TenantEntity) -> TenantEntity: # type: ignore
    """Create a new tenant"""
    pass

@abstractmethod
async def update(self, tenant: TenantEntity):
    """Update a tenant"""
    pass

@abstractmethod
async def delete(self, tenant_id: int):
    """Delete a tenant"""
    pass

@abstractmethod
async def get_by_id(self, tenant_id: int) -> TenantEntity: # type: ignore
    """Get a tenant by ID"""
    pass

@abstractmethod
async def get_waitlist_tenants(self, org_id: int) -> List[TenantEntity]: # type: ignore
    """Get waitlist tenants for an organization"""
    pass

@abstractmethod
async def get_tenant_by_name(self, name: str) -> TenantEntity: #type: ignore
    """Get a tenant by name"""
    pass

@abstractmethod
async def exists(self, tenant: TenantEntity) -> bool: #type: ignore
    """Check if a tenant exists"""
    pass