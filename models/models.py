from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import Column, String
from enum import Enum

class Organization (SQLModel, table=True):
    __tablename__: str = "organizations"
    id: int | None = Field(default=None, primary_key=True)
    business_name: str
    address: str
    number_of_beds: int | None = Field(default=None)
    role: str = Field(default="owner")
    owner_id: int = Field(default=None, foreign_key="users.id")

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
    community_org: str | None
    role: str = Field(default="pending")

class Document (SQLModel, table=True):
    __tablename__: str = "documents"
    id: int | None = Field(default=None, primary_key=True)
    file_name: str | None
    url: str | None
    tenant_id: int | None = Field(default=None, foreign_key='tenants.id')