"""initial migration

Revision ID: a737634f2c04
Revises: ecea7fbb9924
Create Date: 2025-06-25 02:58:35.830200

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a737634f2c04'
down_revision: Union[str, None] = 'ecea7fbb9924'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
