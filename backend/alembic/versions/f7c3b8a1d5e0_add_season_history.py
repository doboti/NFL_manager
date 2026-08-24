"""add season history

Revision ID: f7c3b8a1d5e0
Revises: d4a1c9e6f2b7
Create Date: 2026-08-24 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7c3b8a1d5e0'
down_revision: Union[str, None] = 'd4a1c9e6f2b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('matches', sa.Column('season', sa.Integer(), nullable=False, server_default='1'))
    op.alter_column('matches', 'season', server_default=None)

    op.create_table(
        'season_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('league_id', sa.Integer(), sa.ForeignKey('leagues.id'), nullable=False),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('wins', sa.Integer(), nullable=False),
        sa.Column('losses', sa.Integer(), nullable=False),
        sa.Column('ties', sa.Integer(), nullable=False),
        sa.Column('playoff_result', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_season_history_league_id', 'season_history', ['league_id'])
    op.create_index('ix_season_history_team_id', 'season_history', ['team_id'])


def downgrade() -> None:
    op.drop_index('ix_season_history_team_id', table_name='season_history')
    op.drop_index('ix_season_history_league_id', table_name='season_history')
    op.drop_table('season_history')
    op.drop_column('matches', 'season')
