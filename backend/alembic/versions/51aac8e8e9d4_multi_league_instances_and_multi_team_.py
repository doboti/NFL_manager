"""multi league instances and multi team ownership

Revision ID: 51aac8e8e9d4
Revises: 7cabee942def
Create Date: 2026-08-27 08:04:48.583086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51aac8e8e9d4'
down_revision: Union[str, None] = '7cabee942def'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # nullable first -- the 2 existing league rows ("nfl"/"college") predate
    # this column; `key` and `sport` are identical for them (the very first
    # instance of each sport keeps that simple key), so backfill from `key`
    # before enforcing NOT NULL.
    op.add_column('leagues', sa.Column('sport', sa.String(length=30), nullable=True))
    op.execute("UPDATE leagues SET sport = key WHERE sport IS NULL")
    op.alter_column('leagues', 'sport', nullable=False)

    op.drop_constraint('teams_owner_id_key', 'teams', type_='unique')
    op.drop_index('ix_teams_nfl_team_code', table_name='teams')
    op.create_index(op.f('ix_teams_nfl_team_code'), 'teams', ['nfl_team_code'], unique=False)
    op.create_unique_constraint('uq_teams_league_code', 'teams', ['league_id', 'nfl_team_code'])
    op.create_unique_constraint('uq_teams_owner_league', 'teams', ['owner_id', 'league_id'])

    op.add_column('users', sa.Column('active_team_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_active_team_id', 'users', 'teams', ['active_team_id'], ['id'])
    # Every existing user's single team becomes their active one, so
    # nothing changes behaviorally for anyone who already has a team.
    op.execute(
        "UPDATE users SET active_team_id = teams.id FROM teams WHERE teams.owner_id = users.id"
    )


def downgrade() -> None:
    op.drop_constraint('fk_users_active_team_id', 'users', type_='foreignkey')
    op.drop_column('users', 'active_team_id')
    op.drop_constraint('uq_teams_owner_league', 'teams', type_='unique')
    op.drop_constraint('uq_teams_league_code', 'teams', type_='unique')
    op.drop_index(op.f('ix_teams_nfl_team_code'), table_name='teams')
    op.create_index('ix_teams_nfl_team_code', 'teams', ['nfl_team_code'], unique=True)
    op.create_unique_constraint('teams_owner_id_key', 'teams', ['owner_id'])
    op.drop_column('leagues', 'sport')
