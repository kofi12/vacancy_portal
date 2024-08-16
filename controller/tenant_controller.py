from fastapi import Depends, status, APIRouter
from fastapi.exceptions import HTTPException
from models.models import Tenant
from models.schemas import TenantUpdate, TenantBase
from sqlmodel import Session
from database.db import get_session
from database import tenant_dao

user_router = APIRouter(prefix='/tenants')

@user_router.post('/create-tenant', response_model=Tenant)
def user_create(user_data: TenantBase,
                db: Session = Depends(get_session)):
    return tenant_dao.create_tenant(user_data, db)

@user_router.get('/tenant/{id}')
def tenant_get(id: int,
             db: Session = Depends(get_session)):
    return tenant_dao.get_tenant(id, db)

@user_router.put('/update/{id}')
def tenant_up(id: int, tenant_update: TenantUpdate,
                 db: Session = Depends(get_session)):
    tenant_dao.update_tenant(id, tenant_update, db)

@user_router.delete('/delete/{id}')
def user_delete(id: int,
                db: Session = Depends(get_session)):
    tenant_dao.delete_tenant(id, db)