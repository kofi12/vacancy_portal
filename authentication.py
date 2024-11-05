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
    payload = {}
    scopes = []
    if user_dict.__dict__['display_name'] == "Aaron Haizel":
        scopes = ['tenant:read',
                  'tenant:write',
                  'user:read',
                  'user:write',
        ]
    else:
        scopes = ['waitlist:read',
                  'waitlist:write',
                  'user:read',
                  'user:write'
        ]

    payload['user'] = user_dict.__dict__
    payload['exp'] = 3600
    payload['jti'] = str(uuid.uuid4())
    payload['refresh'] = True
    payload['scopes'] = scopes

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
    try:
        if not access_token:
            return None
        claims = get_token_payload(access_token)
    except BearAuthException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate bearer token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return claims
#TODO: get user from claims, check user role
def has_permission(db: Session = Depends(get_session) , access_token: str = Depends(COOKIE)):
    try:
        if not access_token:
            return None
        claims = get_token_payload(access_token)
        # email = user_data['user']['email']
        # user = get_user_by_email(email, db)
        print(claims['scopes'])

        if claims['scopes'] !=  ['tenant:read', 'tenant:write', 'user:read', 'user:write']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='insufficient permissions'
            )
        return True
    except:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='insufficient permissions',
                headers={"WWW-Authenticate": "Bearer"}
        )