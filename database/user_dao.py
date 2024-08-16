from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from models.models import User
from models.schemas import UserUpdate, UserBase
from sqlmodel import Session, select, delete
from db import get_session

#create user
def create_user(name: str, org: str, role: str, db: Session = Depends(get_session)):
    new_user = UserBase
    statement = select(User).where(name == User.name)
    if  not db.exec(statement):
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'User already exists')
    new_user.name = name
    new_user.organization = org
    new_user.role = role
    db.add(new_user)
    db.commit()

#read user
def get_user(id: int, db: Session = Depends(get_session)) -> User | None:
    statement = select(User).where(id == User.id)
    result = db.exec(statement).first()
    return result

#update user
def update_user(id: int, user_update : UserUpdate,
                            db: Session = Depends(get_session)):
    statement = select(User).where(User.id == id)
    try:
        user = db.exec(statement).first()
    except:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'User does not exist')

    updated_data = user_update.model_dump(exclude_unset=True)


    for k, v in updated_data.items():
        setattr(user, k, v)

    db.commit()
    db.refresh(user)

#delete user
def delete_user(id: int, db: Session = Depends(get_session)):
    try:
        statement = select(User).where(User.id == id)
        user = db.exec(statement)
    except:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            'User does not exist')

    db.delete(user)

