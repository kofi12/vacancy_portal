from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import Column, String
from enum import Enum

class UserRole (str, Enum):
    ADMIN = "admin"
    SCWORKER = "scworker"
    OWNER = "owner"
    PENDING = "pending"

class Tenant (SQLModel, table=True):
    __tablename__: str = "tenants"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    admission_date: datetime | None = Field(default = None)
    discharge_date: datetime | None = Field(default=None)
    waitlist: bool = Field(default=False)

class User (SQLModel, table=True):
    __tablename__: str = "users"
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column("email", String, unique=True))
    first_name: str | None
    last_name: str | None
    organization: str | None
    role: UserRole = Field(default=UserRole.SCWORKER)

class Document (SQLModel, table=True):
    __tablename__: str = "documents"
    id: int | None = Field(default=None, primary_key=True)
    file_name: str | None
    url: str | None
    tenant_id: int | None = Field(default=None, foreign_key='tenants.id')