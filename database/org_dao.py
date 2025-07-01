from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from sqlmodel import Session, select
from models.models import Organization, UserRole
from models.schemas import OrganizationBase, OrganizationUpdate
from db import get_session



#create organization
def create_org(org_data: OrganizationBase,
                        db: Session = Depends(get_session)):
    org_data_dict = org_data.model_dump()
    if not org_exists(org_data_dict['owner_id'], db):
        org = Organization(**org_data_dict)
        db.add(org)
        db.commit()
        db.refresh(org)
        return org
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization already exists")

#get organization
def get_org(id: int, db: Session = Depends(get_session)) -> Organization | None:
    statement = select(Organization).where(id == Organization.id)
    result = db.exec(statement).first()
    return result

def get_all_orgs(db: Session = Depends(get_session)) -> dict:
    statement = select(Organization)
    result = db.exec(statement).all()
    return {'orgs': result}

#update organization
def update_org(org_id: int, org_data: OrganizationUpdate,
               db: Session = Depends(get_session)):
    statement = select(Organization).where(org_id == Organization.id)
    try:
        org = db.exec(statement).first()
    except:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Organization does not exist')

    org = Organization(
        **org_data.model_dump(exclude_unset=True)
    )
    db.commit()

#delete organization
def delete_org(org_id: int, db: Session = Depends(get_session)):
    statement = select(Organization).where(org_id == Organization.id)
    try:
        org = db.exec(statement).first()
    except:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Organization does not exist')
    db.delete(org)
    db.commit()

def org_exists(owner_id: int, db: Session = Depends(get_session)) -> bool:
    org = get_org_by_owner(owner_id, db)
    return org is not None

def get_org_by_owner(owner_id: int,
                    db: Session = Depends(get_session)) -> Organization | None:
    try:
        statement = select(Organization).where(owner_id == Organization.owner_id)
        result = db.exec(statement).first()
        return result
    except:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Organization not found')
        return None

