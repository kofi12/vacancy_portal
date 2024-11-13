from fastapi import Depends, status, APIRouter, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from authentication import SESSION_COOKIE_NAME
from models.models import User
from models.schemas import UserUpdate, UserBase
from sqlmodel import Session, select
from database.db import get_session
from database.user_dao import get_user_by_email, create_user
from fastapi_sso.sso.google import GoogleSSO
from authentication import create_access_token
from dotenv import load_dotenv
import os

load_dotenv()
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME', '')
redirect_uri = 'https://www.vacancyportal-production.up.railway.app/api/auth/callback'

sso = GoogleSSO(GOOGLE_CLIENT_ID,
                GOOGLE_CLIENT_SECRET,
                redirect_uri,
                allow_insecure_http=True
                )

auth_router = APIRouter(prefix='/api/auth')

@auth_router.get('/login', tags=['Auth'])
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
            access_token = create_access_token(user)

        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(SESSION_COOKIE_NAME, access_token)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


