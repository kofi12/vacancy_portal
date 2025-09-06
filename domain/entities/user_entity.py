from enum import Enum
from domain.entities.base_entity import BaseEntity
from datetime import datetime
from dataclasses import dataclass

class Role(Enum):
    OWNER = "owner"
    SCWORKER = "scworker"
    PENDING = "pending"


@dataclass
class UserEntity(BaseEntity):
    """"User Entity"""
    _email: str
    _first_name: str
    _last_name: str
    _community_org: str | None = None
    _role: Role = Role.PENDING

    def __init__(self, id: int | None, created_at: datetime, email: str, first_name: str,
                 last_name: str, community_org: str, role: Role
                 ):
        super().__init__(id, created_at)
        self._email = email
        self._first_name = first_name
        self._last_name = last_name
        self._community_org = community_org


    def has_role_assigned(self) -> bool:
        return self._role != Role.PENDING

    @classmethod
    def create_user(cls,
                    email: str,
                    first_name: str,
                    last_name: str,
                    community_org: str) -> 'UserEntity':
        """Factory method for creating new users"""
        return cls(id=None,
                   created_at=datetime.now(),
                   email=email,
                   first_name=first_name,
                   last_name=last_name,
                   community_org=community_org,
                   role=Role.PENDING)

