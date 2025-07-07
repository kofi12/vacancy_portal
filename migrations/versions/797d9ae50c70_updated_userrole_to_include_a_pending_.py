"""updated UserRole to include a PENDING role

Revision ID: 797d9ae50c70
Revises: e59d876c704d
Create Date: 2025-06-25 19:48:04.797407

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '797d9ae50c70'
down_revision: Union[str, None] = 'e59d876c704d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update all existing values to lowercase (optional, for consistency)
    op.execute("UPDATE users SET role = LOWER(role)")
    # Now alter the column to use String, with explicit cast
    op.alter_column(
        'users',
        'role',
        existing_type=sa.VARCHAR(),
        type_=sa.String(),
        nullable=False,
        postgresql_using="role::varchar"
    )


def downgrade() -> None:
    op.alter_column(
        'users',
        'role',
        existing_type=sa.String(),
        type_=sa.VARCHAR(),
        nullable=True
    )
