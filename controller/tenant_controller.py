from fastapi import Depends, status, APIRouter, UploadFile
from models.models import Tenant
from models.schemas import TenantUpdate, TenantBase, DocumentDown
from sqlmodel import Session
from database.db import get_session
from database import tenant_dao
from controller.upload_pdf import upload_f
from controller.download_pdf import download_f

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

@tenant_router.put('/update/{id}', response_model_exclude_unset=True)
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

@tenant_router.post('/upload-pdf/{id}')
def upload(file: UploadFile, id: int, db: Session = Depends(get_session)):
    return upload_f(file, id, db)

@tenant_router.get('/download-pdf/{id}')
def download(id: int, db: Session = Depends(get_session)):
    return download_f(id, db)