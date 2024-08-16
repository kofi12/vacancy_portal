from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import Column, String

class Tenant (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    admission_date: datetime | None = Field(default = None)
    discharge_date: datetime | None = Field(default=None)
    waitlist: bool = Field(default=False)

class User (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column("email", String, unique=True))
    name: str
    organization: str
    role: str
    hashed_password: str