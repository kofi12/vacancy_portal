"""Initial revision

Revision ID: d79d87a9bbd2
Revises: a737634f2c04
Create Date: 2025-06-25 16:16:27.305468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'd79d87a9bbd2'
down_revision: Union[str, None] = 'a737634f2c04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
