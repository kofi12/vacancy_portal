from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from models.models import Tenant
from models.schemas import TenantBase, TenantUpdate
from sqlmodel import Session, select, delete
from db import get_session

#create tenant
def create_tenant(name: str, db: Session = Depends(get_session)):
    new_tenant = TenantBase
    statement = select(Tenant).where(name == Tenant.name)
    if  not db.exec(statement):
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Tenant already exists')
    new_tenant.name = name
    db.add(new_tenant)
    db.commit()

#read tenant
def get_tenant(id: int, db: Session = Depends(get_session)) -> Tenant | None:
    statement = select(Tenant).where(id == Tenant.id)
    result = db.exec(statement).first()
    return result

#update tenant
def update_tenant(id: int, tenant_update : TenantUpdate,
                            db: Session = Depends(get_session)):
    statement = select(Tenant).where(Tenant.id == id)
    try:
        tenant = db.exec(statement).first()
    except:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Tenant does not exist')

    updated_data = tenant_update.model_dump(exclude_unset=True)


    for k, v in updated_data.items():
        setattr(tenant, k, v)

    db.commit()
    db.refresh(tenant)

#delete tenant
def delete_tenant(id: int, db: Session = Depends(get_session)):
    try:
        statement = select(Tenant).where(Tenant.id == id)
        tenant = db.exec(statement)
    except:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            'Tenant does not exist')

    db.delete(tenant)

#get all tenants
def get_tenants(db: Session = Depends(get_session)):
    tenants = []
    statement = select(Tenant)
    tenants = db.exec(statement).all()

    return {'tenants': tenants}
