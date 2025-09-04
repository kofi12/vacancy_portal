from domain.entities.base_entity import BaseEntity
from datetime import datetime

class UserEntity(BaseEntity):
    """"User Entity"""
    _email: str
    _first_name: str
    _last_name: str
    _community_org: str | None = None
    _role: str = "pending"

    def __init__(self, id: int | None, created_at: datetime, email: str, first_name: str,
                 last_name: str, community_org: str, role: str
                 ):
        super().__init__(id, created_at)

    @property
    def email(self) -> str:
        if not self._email:
            raise ValueError("no email exists for user")
        return self._email

    @email.setter
    def email(self, email: str):
        if not email or email.strip() == "":
            raise ValueError("email cannot be empty")
        self._email = email

    @property
    def first_name(self) -> str:
        if not self._first_name:
            raise ValueError("no first name exists for user")
        return self._first_name

    @first_name.setter
    def first_name(self, first_name: str):
        if not first_name or first_name.strip() == "":
            raise ValueError("First name cannot be empty")
        self._first_name = first_name

    @property
    def last_name(self) -> str:
        if not self._last_name:
            raise ValueError("no last name exists for user")
        return self._last_name

    @last_name.setter
    def last_name(self, last_name: str):
        if not last_name or last_name.strip() == "":
            raise ValueError("Last name cannot be empty")
        self._last_name = last_name

    @property
    def community_org(self) -> str:
        if not self._community_org:
            raise ValueError("User doesn't belong to an organization")
        return self._community_org

    @community_org.setter
    def community_org(self, org: str):
        if not org or not org.strip() == "":
            raise ValueError("Organization cannot be empty")
        self._community_org = org

    @property
    def role(self) -> str:
        if not self.role:
            raise ValueError("User has no role assigned")
        return self._role

    @role.setter
    def role(self, role: str):
        if not role:
            raise ValueError("No role selected or given")
        self._role = role

