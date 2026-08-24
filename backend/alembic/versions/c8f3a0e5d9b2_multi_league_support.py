"""multi-league support: game_clock, league key, team/player league_id

Revision ID: c8f3a0e5d9b2
Revises: a2e9f6c1b4d7
Create Date: 2026-08-24 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8f3a0e5d9b2'
down_revision: Union[str, None] = 'a2e9f6c1b4d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # game_clock: singleton table for the dev virtual clock, decoupled from
    # any one league so leagues can be freely multiplied.
    op.create_table(
        'game_clock',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('time_offset_seconds', sa.Integer(), nullable=False, server_default='0'),
    )
    op.execute(
        """
        INSERT INTO game_clock (time_offset_seconds)
        SELECT COALESCE(MAX(time_offset_seconds), 0) FROM leagues
        """
    )

    # leagues.key: stable identifier ("nfl", "college") instead of matching by name
    op.add_column('leagues', sa.Column('key', sa.String(length=30), nullable=True))
    op.execute("UPDATE leagues SET key = 'nfl' WHERE key IS NULL")
    op.alter_column('leagues', 'key', nullable=False)
    op.create_unique_constraint('uq_leagues_key', 'leagues', ['key'])

    op.drop_column('leagues', 'time_offset_seconds')

    # teams.league_id: every existing team belongs to the (only, so far) NFL league
    op.add_column('teams', sa.Column('league_id', sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE teams SET league_id = (SELECT id FROM leagues WHERE key = 'nfl')
        WHERE league_id IS NULL
        """
    )
    op.alter_column('teams', 'league_id', nullable=False)
    op.create_foreign_key('fk_teams_league_id', 'teams', 'leagues', ['league_id'], ['id'])
    op.create_index('ix_teams_league_id', 'teams', ['league_id'])

    # players.league_id: same backfill
    op.add_column('players', sa.Column('league_id', sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE players SET league_id = (SELECT id FROM leagues WHERE key = 'nfl')
        WHERE league_id IS NULL
        """
    )
    op.alter_column('players', 'league_id', nullable=False)
    op.create_foreign_key('fk_players_league_id', 'players', 'leagues', ['league_id'], ['id'])
    op.create_index('ix_players_league_id', 'players', ['league_id'])


def downgrade() -> None:
    op.drop_index('ix_players_league_id', table_name='players')
    op.drop_constraint('fk_players_league_id', 'players', type_='foreignkey')
    op.drop_column('players', 'league_id')

    op.drop_index('ix_teams_league_id', table_name='teams')
    op.drop_constraint('fk_teams_league_id', 'teams', type_='foreignkey')
    op.drop_column('teams', 'league_id')

    op.add_column('leagues', sa.Column('time_offset_seconds', sa.Integer(), nullable=False, server_default='0'))
    op.drop_constraint('uq_leagues_key', 'leagues', type_='unique')
    op.drop_column('leagues', 'key')

    op.drop_table('game_clock')
