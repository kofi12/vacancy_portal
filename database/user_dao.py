from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from sqlmodel import Session, select
from models.models import User, UserRole
from models.schemas import UserUpdate, UserBase
from .db import get_session


#create user
def create_user(user_data: UserBase,
                db: Session = Depends(get_session)):
    user_data_dict = user_data.model_dump()

    if not user_exists(user_data, db):
        user = User(
            **user_data_dict,
            role = UserRole.PENDING,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User with email already exists")

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

    user = User(
        **updated_data
    )
    # for k, v in updated_data.items():
    #     setattr(user, k, v)
    db.commit()
    # db.refresh(user)

#delete user
def delete_user(id: int, db: Session = Depends(get_session)):
    try:
        statement = select(User).where(User.id == id)
        user = db.exec(statement)
    except:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            'User does not exist')

    db.delete(user)

def user_exists(user_data: UserBase,
                session: Session = Depends(get_session)) -> bool:
    email = user_data.email
    user = get_user_by_email(email, session)
    if user is None:
        return False
    return True

def get_user_by_email(email: str,
                     db: Session = Depends(get_session)):
    statement = select(User).where(User.email == email)
    result = db.exec(statement).first()
    return result

def update_user_role(user_id: int, role: UserRole, db: Session = Depends(get_session)):
    statement = select(User).where(User.id == user_id)
    user = db.exec(statement).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = role
    db.add(user)
    db.commit()
    db.refresh(user)
    return user