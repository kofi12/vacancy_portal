from passlib.context import CryptContext
from jose import JWTError, jwt
from jose.constants import ALGORITHMS
from fastapi.security import OAuth2PasswordBearer, APIKeyCookie
from fastapi import Depends, HTTPException, status
from fastapi_sso.sso.base import OpenID
from models.models import User
from sqlmodel import Session, select
from database.user_dao import get_user_by_email
import uuid
from database.db import get_session
from pathlib import Path
from dotenv import load_dotenv
import os

directory_path = Path(__file__).parent
env_file_path = directory_path / '.env'

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "default_secret_key")
JWT_ALGO = os.getenv("JWT_ALGO", "default_secret_key")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "default_session_cookie_name")


COOKIE = APIKeyCookie(name=SESSION_COOKIE_NAME, auto_error=False)

class BearAuthException(Exception):
    pass


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(user_dict: OpenID | None):
    payload = {}
    payload['user'] = user_dict.__dict__
    payload['exp'] = 3600
    payload['jti'] = str(uuid.uuid4())
    payload['refresh'] = True

    encoded_jwt = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGO
    )
    return encoded_jwt


def get_token_payload(session_token: str):
    try:
        print("before decode")
        payload = jwt.decode(
            token=session_token,
            key=JWT_SECRET,
            algorithms=[JWT_ALGO]
        )
        user = payload['user']
        if user is None:
            raise BearAuthException("Token could not be validated")
        return {
            'user' : user
        }
    except JWTError:
        raise BearAuthException("Token could not be validated")


# def authenticate_user(db: Session, username: str, password: str, provider: str):
#     user = db.query(User).filter(User.username == username).first()
#     if not user:
#         return False
#     if not verify_password(password, user.password):
#         return False
#     return user


def get_current_user(db: Session = Depends(get_session), session_token: str = Depends(COOKIE)):
    try:
        if not session_token:
            return None
        user_data = get_token_payload(session_token)
        email = user_data['user']['email']
    except BearAuthException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate bearer token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        return None
    return user

def has_role(db: Session = Depends(get_session) , session_token: str = Depends(COOKIE)):
    try:
        if not session_token:
            return None
        print("here")
        user_data = get_token_payload(session_token)
        print(user_data)
        email = user_data['user']['email']
        user = get_user_by_email(email, db)

        if user and user.role == 'member':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='insufficient permissions'
            )
        return user
    except:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='insufficient permissions',
                headers={"WWW-Authenticate": "Bearer"}
        )