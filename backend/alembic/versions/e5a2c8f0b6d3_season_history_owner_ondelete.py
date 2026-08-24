"""season_history.owner_id ON DELETE SET NULL

Revision ID: e5a2c8f0b6d3
Revises: d1e7b3c9a4f6
Create Date: 2026-08-24 19:30:00.000000

Deleting a bot user on team takeover/release started failing with a
ForeignKeyViolation the moment that bot had any season_history row (e.g.
its team had already finished a season while bot-controlled) -- the plain
FK added in d1e7b3c9a4f6 blocked the delete outright. Bot achievements
don't matter, so let the delete proceed and just null the reference.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e5a2c8f0b6d3'
down_revision: Union[str, None] = 'd1e7b3c9a4f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('fk_season_history_owner_id', 'season_history', type_='foreignkey')
    op.create_foreign_key(
        'fk_season_history_owner_id', 'season_history', 'users', ['owner_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_season_history_owner_id', 'season_history', type_='foreignkey')
    op.create_foreign_key('fk_season_history_owner_id', 'season_history', 'users', ['owner_id'], ['id'])
