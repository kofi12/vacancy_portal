from fastapi import Depends, status, APIRouter
from models.models import Tenant
from models.schemas import TenantUpdate, TenantBase
from sqlmodel import Session
from database.db import get_session
from database import tenant_dao

tenant_router = APIRouter(prefix='/tenants')

@tenant_router.post('/create-tenant', response_model=Tenant)
def tenant_create(user_data: TenantBase,
                db: Session = Depends(get_session)):
    return tenant_dao.create_tenant(user_data, db)

@tenant_router.post('/create-waitlist-tenant', response_model=Tenant)
def waitlist_tenant_create(user_data: TenantBase,
                db: Session = Depends(get_session)):
    return tenant_dao.create_waitlist_tenant(user_data, db)

@tenant_router.get('/tenant/{id}')
def tenant_get(id: int,
             db: Session = Depends(get_session)):
    return tenant_dao.get_tenant(id, db)

@tenant_router.put('/update/{id}')
def tenant_up(id: int, tenant_update: TenantUpdate,
                 db: Session = Depends(get_session)):
    tenant_dao.update_tenant(id, tenant_update, db)

@tenant_router.delete('/delete/{id}')
def user_delete(id: int,
                db: Session = Depends(get_session)):
    tenant_dao.delete_tenant(id, db)

@tenant_router.get('/all-tenants')
def get_all_tenants(db: Session = Depends(get_session)):
    return tenant_dao.get_tenants(db)

@tenant_router.get('/waitlist')
def get_waitlist(db: Session = Depends(get_session)):
    return tenant_dao.get_waitlist_tenants(db)