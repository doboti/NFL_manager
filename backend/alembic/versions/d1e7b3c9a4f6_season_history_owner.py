"""add season_history.owner_id

Revision ID: d1e7b3c9a4f6
Revises: c8f3a0e5d9b2
Create Date: 2026-08-24 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e7b3c9a4f6'
down_revision: Union[str, None] = 'c8f3a0e5d9b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('season_history', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_season_history_owner_id', 'season_history', 'users', ['owner_id'], ['id'])
    op.create_index('ix_season_history_owner_id', 'season_history', ['owner_id'])
    # Best-effort backfill: attribute existing rows to the team's *current*
    # owner (we don't have historical per-season ownership on file).
    op.execute(
        """
        UPDATE season_history sh
        SET owner_id = t.owner_id
        FROM teams t
        WHERE t.id = sh.team_id AND sh.owner_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index('ix_season_history_owner_id', table_name='season_history')
    op.drop_constraint('fk_season_history_owner_id', 'season_history', type_='foreignkey')
    op.drop_column('season_history', 'owner_id')
