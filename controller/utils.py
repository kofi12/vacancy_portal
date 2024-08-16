from datetime import datetime, timedelta, timezone
from fastapi import Depends
from sqlmodel import Session
from database.db import get_session
import bcrypt


def hash_passwd(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode('utf-8')

def verify_passwd(password: str, hash: str) -> bool:
    password_byte_enc = password.encode('utf-8')
    hash_byte_enc = hash.encode('utf-8')
    return bcrypt.checkpw(password = password_byte_enc , hashed_password = hash_byte_enc)

def authenticate_user(user_name: str, password: str,
                      session: Session = Depends(get_session)):
    from database.user_dao import get_user_by_name

    user = get_user_by_name(user_name, session)
    if not user:
        return False
    if not verify_passwd(password, user.hashed_password):
        return False
    return user
