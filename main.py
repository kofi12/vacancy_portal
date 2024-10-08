from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from database import db
from controller import tenant_controller, user_controller


app = FastAPI()
SQLModel.metadata.create_all(db.engine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(tenant_controller.tenant_router)
app.include_router(user_controller.user_router)

@app.get('/')
async def root():
    return {'message': 'Hello World'}