from fastapi import Depends, status, APIRouter, UploadFile
from fastapi.security import SecurityScopes, OAuth2AuthorizationCodeBearer
from models.models import Tenant
from models.schemas import TenantUpdate, TenantBase
from sqlmodel import Session
from database.db import get_session
from database import tenant_dao
from controller.upload_pdf import upload_f
from controller.download_pdf import download_f
from models.models import User
from authentication import require_roles
import os

# oauth2_scheme = OAuth2AuthorizationCodeBearer(authorizationUrl="https://accounts.google.com/o/oauth2/v2/auth",
#                                               tokenUrl="token",
#                                               scopes={"tenant:read": "Read tenant data", "tenant:write": "Write tenant data"}
#                                               )

tenant_router = APIRouter(prefix='/api/tenants')


@tenant_router.post('/create-tenant', response_model=Tenant, tags=["Tenants"])
def tenant_create(security_scopes: SecurityScopes, user_data: TenantBase,
                db: Session = Depends(get_session), user: User = Depends(require_roles("admin", "owner"))):
    return tenant_dao.create_tenant(user_data, db)

@tenant_router.post('/create-waitlist-tenant', response_model=Tenant, tags=["Tenants"])
def waitlist_tenant_create(user_data: TenantBase,
                db: Session = Depends(get_session), user: User = Depends(require_roles("scworker", "admin"))):
    return tenant_dao.create_waitlist_tenant(user_data, db)

@tenant_router.get('/tenant/{id}', tags=["Tenants"])
def tenant_get(t_id: int,
               db: Session = Depends(get_session)):
    return tenant_dao.get_tenant(t_id, db)

@tenant_router.put('/update/{id}', response_model_exclude_unset=True, tags=["Tenants"])
def tenant_up(t_id: int, tenant_update: TenantUpdate,
              db: Session = Depends(get_session), user: User = Depends(require_roles("admin", "owner"))):
    tenant_dao.update_tenant(t_id, tenant_update, db)

@tenant_router.delete('/delete/{id}', tags=["Tenants"])
def tenant_delete(t_id: int,
                db: Session = Depends(get_session), user: User = Depends(require_roles("admin", "owner"))):
    tenant_dao.delete_tenant(t_id, db)

@tenant_router.get('/all-tenants', tags=["Tenants"])
def get_all_tenants(db: Session = Depends(get_session), user: User = Depends(require_roles("admin", "owner"))):
    return tenant_dao.get_tenants(db)

@tenant_router.get('/waitlist', tags=["Tenants"])
def get_waitlist(db: Session = Depends(get_session)):
    return tenant_dao.get_waitlist_tenants(db)

@tenant_router.post('/upload-pdf/{id}', tags=["Tenants"])
def upload(file: UploadFile, t_id: int, db: Session = Depends(get_session), user: User = Depends(require_roles("scworker"))):
    return upload_f(file, t_id, db)

@tenant_router.get('/download-pdf/{id}', tags=["Tenants"])
def download(t_id: int, db: Session = Depends(get_session), user: User = Depends(require_roles("admin", "owner"))):
    return download_f(t_id, db)