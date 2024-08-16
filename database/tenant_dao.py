from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from models.models import Tenant
from models.schemas import TenantBase, TenantUpdate
from sqlmodel import Session, select
from db import get_session

#create tenant
def create_tenant(tenant_data: TenantBase,
                  db: Session = Depends(get_session)):
    tenant_data_dict = tenant_data.model_dump()

    if not tenant_exists(tenant_data, db):
        tenant = Tenant(
            **tenant_data_dict
        )

        db.add(tenant)
        db.commit()
        return tenant

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant with email already exists")



#read tenant
def get_tenant(id: int,
               db: Session = Depends(get_session)) -> Tenant | None:
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

    tenant = Tenant(
        **updated_data
    )
    # for k, v in updated_data.items():
    #     setattr(tenant, k, v)
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

def tenant_exists(tenant_data: TenantBase,
                db: Session = Depends(get_session)) -> bool:
    name = tenant_data.name
    tenant = get_tenant_by_name(name, db)
    if tenant is None:
        return False
    return True

def get_tenant_by_name(name: str,
                     db: Session = Depends(get_session)):
    statement = select(Tenant).where(Tenant.name == name)
    result = db.exec(statement).first()
    return result

