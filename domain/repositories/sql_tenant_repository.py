from typing import List
from repositories.interfaces.tenant_repository import TenantRepository
from domain.entities.tenant_entity import TenantEntity
from models.models import Tenant
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

class SQLTenantRepository(TenantRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, tenant: Tenant) -> TenantEntity:
        """Create a new tenant"""
        tenant_model = Tenant(
                    name=tenant.name,
                    admission_date=tenant.admission_date,
                    discharge_date=tenant.discharge_date,
                    waitlist=tenant.waitlist,
                    organization_id=tenant.organization_id
        )

        tenant_entity = TenantEntity(
                    name=tenant.name,
                    admission_date=tenant.admission_date,
                    organization_id=tenant.organization_id,
        )

        self._session.add(tenant_model)
        await self._session.commit()
        await self._session.refresh(tenant_model)

        return tenant_entity

    async def update(self, tenant_id: int):
        """Update a tenant"""

        stmt = select(Tenant).where(Tenant.id == tenant_id).limit(1)
        result = await self._session.exec(stmt)
        tenant_entity = result



    async def delete(self, tenant_id: int):
        pass

    async def get_by_id(self, tenant_id: int) -> TenantEntity:  # pyright: ignore[reportReturnType]
        pass

    async def get_waitlist_tenants(self, org_id: int) -> List[TenantEntity]:  # pyright: ignore[reportReturnType]
        pass

    async def get_tenant_by_name(self, name: str) -> TenantEntity:  # pyright: ignore[reportReturnType]
        pass

    async def exists(self, tenant: TenantEntity) -> bool:  # pyright: ignore[reportReturnType]
        pass