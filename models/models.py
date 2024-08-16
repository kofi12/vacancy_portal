from sqlmodel import SQLModel, Field
from datetime import datetime

class Tenant (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    admission_date: datetime | None = Field(default = None)
    discharge_date: datetime | None = Field(default=None)

class User (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    organization: str
    role: str
    hashed_password: str