"""add player injured_until

Revision ID: 8289f1765be0
Revises: e5a2c8f0b6d3
Create Date: 2026-08-24 19:33:40.484870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8289f1765be0'
down_revision: Union[str, None] = 'e5a2c8f0b6d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("players", sa.Column("injured_until", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("players", "injured_until")
