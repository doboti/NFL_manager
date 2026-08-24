"""add player base_overall

Revision ID: a2e9f6c1b4d7
Revises: f7c3b8a1d5e0
Create Date: 2026-08-24 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2e9f6c1b4d7'
down_revision: Union[str, None] = 'f7c3b8a1d5e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('players', sa.Column('base_overall', sa.Integer(), nullable=True))
    op.execute('UPDATE players SET base_overall = overall WHERE base_overall IS NULL')
    op.alter_column('players', 'base_overall', nullable=False)


def downgrade() -> None:
    op.drop_column('players', 'base_overall')
