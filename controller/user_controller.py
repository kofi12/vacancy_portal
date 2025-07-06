from fastapi import Depends, status, APIRouter
from fastapi.exceptions import HTTPException
from models.models import User
from models.schemas import UserUpdate, UserBase
from sqlmodel import Session, select
from database.db import get_session
from database import user_dao
from authentication import require_roles

user_router = APIRouter(prefix='/api/users')

@user_router.get('/user/{id}', response_model=User, tags=["Users"])
def user_get(id: int,
             db: Session = Depends(get_session), user: User = Depends(require_roles("admin", "scworker"))):
    return user_dao.get_user(id, db)

@user_router.put('/update/{id}', response_model_exclude_unset=True, tags=["Users"])
def user_update(id: int, user_update: UserUpdate,
                 db: Session = Depends(get_session), user: User = Depends(require_roles("admin", "scworker"))):
    user_dao.update_user(id, user_update, db)

@user_router.delete('/delete/{id}', tags=["Users"])
def user_delete(id: int,
                db: Session = Depends(get_session), user: User = Depends(require_roles("admin", "scworker"))):
    user_dao.delete_user(id, db)