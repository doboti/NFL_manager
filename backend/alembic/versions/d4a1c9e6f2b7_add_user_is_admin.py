"""add user is_admin

Revision ID: d4a1c9e6f2b7
Revises: 11e5dd940811
Create Date: 2026-08-24 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4a1c9e6f2b7'
down_revision: Union[str, None] = '11e5dd940811'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column('users', 'is_admin', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
