from fastapi import Depends, status, APIRouter, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from authentication import SESSION_COOKIE_NAME, get_current_user_with_scopes
from models.models import User
from models.schemas import UserUpdate, UserBase
from sqlmodel import Session, select
from database.db import get_session
from database.user_dao import get_user_by_email, create_user, update_user_role
from fastapi_sso.sso.google import GoogleSSO
from authentication import create_access_token
from dotenv import load_dotenv
import os

load_dotenv()
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME', '')
redirect_uri = 'http://localhost:8000/api/auth/callback'

sso = GoogleSSO(GOOGLE_CLIENT_ID,
                GOOGLE_CLIENT_SECRET,
                redirect_uri,
                allow_insecure_http=True
                )

auth_router = APIRouter(prefix='/api/auth')

@auth_router.get('/token', tags=['Auth'])
async def auth_init():
    with sso:
        return await sso.get_login_redirect()

@auth_router.get("/callback", tags=['Auth'])
async def auth_callback(request: Request, db: Session = Depends(get_session)):
    """Verify login"""
    try:
        with sso:
            user = await sso.verify_and_process(request)

            email = user.__dict__['email']

            # check if user exists in database
            db_user = get_user_by_email(email, db)
            if not db_user:
                user_data = UserBase(
                    email=email,
                    first_name=user.__dict__['first_name'],
                    last_name=user.__dict__['last_name'],
                )
                db_user = create_user(user_data, db)

            access_token = create_access_token(user, db)

        # Return the token in the response body as per OAuth2 standard
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")

@auth_router.post("/set-role", tags=["Auth"])
def set_role(role: str, current_user: User = Depends(get_current_user_with_scopes), db: Session = Depends(get_session)):
    if current_user.role != "pending":
        raise HTTPException(status_code=400, detail="Role already set.")
    if current_user.id is None:
        raise HTTPException(status_code=400, detail="User ID is missing.")
    update_user_role(current_user.id, role, db)
    return {"message": "Role updated successfully"}


