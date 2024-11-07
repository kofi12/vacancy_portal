from sys import prefix
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from database import db
from controller import tenant_controller, user_controller
from auth import auth

app = FastAPI()
# SQLModel.metadata.create_all(db.engine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://www.vacancyportal.ca"],  # Adjust this as needed
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