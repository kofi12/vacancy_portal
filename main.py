from sys import prefix
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from database import db
from controller import tenant_controller, user_controller
from auth import auth
from alembic.config import Config
from alembic import command
import uvicorn

app = FastAPI()
ALEMBIC_CONFIG = "alembic.ini"

def run_migrations():
    """
    Apply all pending Alembic migrations.
    """
    alembic_cfg = Config(ALEMBIC_CONFIG)
    command.upgrade(alembic_cfg, "head")


@app.on_event("startup")
async def startup_event():
    """
    Run migrations during the app startup.
    """
    try:
        run_migrations()
    except Exception as e:
        import traceback
        print("Error during migration startup:", e)
        traceback.print_exc()
        raise


# SQLModel.metadata.create_all(db.engine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://www.vacancyportal.ca", "https://www.vacancyportal.ca"],  # Adjust this as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(tenant_controller.tenant_router)
app.include_router(user_controller.user_router)
app.include_router(auth.auth_router)

@app.get('/')
async def root():
    return {'message': 'Hello World'}