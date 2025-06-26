from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from sqlmodel import Session, select
from models.models import Organization, UserRole
from models.schemas import OrganizationBase, OrganizationUpdate
from db import get_session



#create organization
def create_organization(org_data: OrganizationBase,
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
def get_organization(id: int, db: Session = Depends(get_session)) -> Organization | None:
    statement = select(Organization).where(id == Organization.id)
    result = db.exec(statement).first()
    return result

#update organization

#delete organization


def org_exists(owner_id: int, db: Session = Depends(get_session)) -> bool:
    org = get_org_by_owner(owner_id, db)
    return org is not None

def get_org_by_owner(owner_id: int,
                             db: Session = Depends(get_session)) -> Organization | None:
    statement = select(Organization).where(owner_id == Organization.owner_id)
    result = db.exec(statement).first()
    return result