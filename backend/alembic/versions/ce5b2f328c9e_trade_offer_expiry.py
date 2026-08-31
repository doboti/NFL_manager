"""trade offer expiry

Revision ID: ce5b2f328c9e
Revises: a1dfdc274c54
Create Date: 2026-08-31 19:30:33.229502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce5b2f328c9e'
down_revision: Union[str, None] = 'a1dfdc274c54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # autogenerate doesn't diff native enum value lists -- added by hand.
    op.execute("ALTER TYPE trade_status ADD VALUE IF NOT EXISTS 'EXPIRED'")

    op.add_column('trade_offers', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))

    # Existing PENDING rows predate this column -- backfill from created_at
    # so a long-stuck offer (e.g. sent to a human who never responded)
    # expires on the very next check instead of sitting there forever with
    # no expiry at all.
    op.execute(
        "UPDATE trade_offers SET expires_at = created_at + interval '24 hours' "
        "WHERE status = 'PENDING' AND expires_at IS NULL"
    )


def downgrade() -> None:
    op.drop_column('trade_offers', 'expires_at')
    # Postgres has no ALTER TYPE ... DROP VALUE -- leaving 'EXPIRED' in the
    # enum on downgrade is harmless (unused, same as any other unreferenced
    # enum member).
