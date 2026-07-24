"""add ssh key sync status columns

Revision ID: b2c3d4e5f6a7
Revises: f9a1b2c3d4e5
Create Date: 2026-07-13 13:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "f9a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_ssh_keys",
        sa.Column(
            "sync_status", sa.String(10), nullable=False, server_default="pending"
        ),
    )
    op.add_column("user_ssh_keys", sa.Column("sync_error", sa.Text(), nullable=True))
    # 已有 gitea_key_id 的记录视为已同步
    op.execute(
        "UPDATE user_ssh_keys SET sync_status = 'synced' WHERE gitea_key_id IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column("user_ssh_keys", "sync_error")
    op.drop_column("user_ssh_keys", "sync_status")
