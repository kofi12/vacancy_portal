from datetime import UTC, datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from jose.constants import ALGORITHMS
from fastapi.security import OAuth2PasswordBearer, APIKeyCookie
from fastapi import Depends, HTTPException, status, Security
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
JWT_SECRET = os.getenv("JWT_SECRET", '')
JWT_ALGO = os.getenv("JWT_ALGO", '')
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", '')
COOKIE = APIKeyCookie(name=SESSION_COOKIE_NAME, auto_error=False)

# create a function to return scopes, to be used as a dependency
class BearAuthException(Exception):
    pass

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(user_dict: OpenID | None):
    if user_dict is None:
        raise ValueError("user_dict cannot be None")
    payload = {
        "sub": user_dict.email,# unique identifier       # user role if needed
        "exp": datetime.now(UTC) + timedelta(seconds=3600),
        "jti": str(uuid.uuid4()),
        "scopes": [],
    }
    encoded_jwt = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGO
    )
    return encoded_jwt

def get_token_payload(session_token: str):
    try:
        payload = jwt.decode(
            token=session_token,
            key=JWT_SECRET,
            algorithms=[ALGORITHMS.HS256]
        )

        if payload is None:
            raise BearAuthException("Token could not be validated")
        return {
            'claims' : payload
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

def get_current_user(db: Session = Depends(get_session), access_token: str = Depends(COOKIE)):
    if not access_token:
        return None
    try:
        claims = get_token_payload(access_token)
        email = claims['claims'].get("sub")
        if not email:
            raise BearAuthException("Token missing subject")

        user = get_user_by_email(email, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except BearAuthException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate bearer token",
            headers={"WWW-Authenticate": "Bearer"}
        )

def require_roles(*allowed_roles: str):
    def role_dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            allowed = ", ".join(allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the roles [{allowed}], but user role is '{current_user.role}'."
            )
        return current_user
    return role_dependency
