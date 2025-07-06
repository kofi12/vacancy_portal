from fastapi import Depends, APIRouter
from models.models import Organization
from models.schemas import OrganizationBase, OrganizationUpdate
from sqlmodel import Session
from database.db import get_session
from database import org_dao
from authentication import require_roles

org_router = APIRouter(prefix='/api/orgs')

@org_router.get('/org/{id}', response_model= Organization, tags=["Organizations"])
def get_org(id: int, db: Session = Depends(get_session)):
    return org_dao.get_org(id, db)

@org_router.get('/all-orgs', response_model=dict, tags=["Organizations"])
def get_orgs(db: Session = Depends(get_session)):
    return org_dao.get_all_orgs(db)

@org_router.post('/create-org', response_model=Organization, tags=["Organizations"])
def create_org(org_data: OrganizationBase, db: Session = Depends(get_session)):
    return org_dao.create_org(org_data, db)

@org_router.put('/update-org/{id}', response_model_exclude_unset=True, tags=["Organizations"])
def update_org(id: int, org_data: OrganizationUpdate, db: Session = Depends(get_session)):
    return org_dao.update_org(id, org_data, db)

@org_router.delete('/delete-org/{id}', tags=["Organizations"])
def delete_org(id: int, db: Session = Depends(get_session)):
    return org_dao.delete_org(id, db)