"""add status fields to monitor

Revision ID: e94a2ee8b928
Revises: a0dd4ade47fe
Create Date: 2026-09-24 14:04:01.073929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e94a2ee8b928'
down_revision: Union[str, Sequence[str], None] = 'a0dd4ade47fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('monitors', sa.Column('last_status', sa.String(length=255), nullable=True))
    op.add_column('monitors', sa.Column('last_checked', sa.DateTime(), nullable=True))
    op.add_column('monitors', sa.Column('last_response_time', sa.Float(), nullable=True))
    op.add_column('monitors', sa.Column('last_error', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('monitors', 'last_error')
    op.drop_column('monitors', 'last_response_time')
    op.drop_column('monitors', 'last_checked')
    op.drop_column('monitors', 'last_status')
