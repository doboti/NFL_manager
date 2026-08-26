"""add trade offer respond_at

Revision ID: d3db337ccb99
Revises: 8289f1765be0
Create Date: 2026-08-26 15:44:00.074849

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3db337ccb99'
down_revision: Union[str, None] = '8289f1765be0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("trade_offers", sa.Column("respond_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("trade_offers", "respond_at")
