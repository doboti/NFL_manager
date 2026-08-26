"""add player potential

Revision ID: 7cabee942def
Revises: d3db337ccb99
Create Date: 2026-08-26 19:04:48.787073

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7cabee942def'
down_revision: Union[str, None] = 'd3db337ccb99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("players", sa.Column("potential", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("players", "potential")
