"""replace MongoDB stores with PostgreSQL tables

Revision ID: 9a7f2c1d4e5f
Revises: 58dde79f6b34
Create Date: 2026-08-19 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a7f2c1d4e5f"
down_revision: Union[str, Sequence[str], None] = "58dde79f6b34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 邮箱验证码：email+purpose 唯一，upsert 覆盖旧码
    op.create_table(
        "email_verification_codes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.String(length=50), nullable=False),
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", "purpose", name="uq_email_code_purpose"),
    )
    op.create_index(
        "ix_email_verification_codes_email_purpose",
        "email_verification_codes",
        ["email", "purpose"],
        unique=False,
    )

    # 站内通知：替代 MongoDB notifications 集合
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("recipient_id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("link", sa.String(length=500), nullable=True),
        sa.Column("source_type", sa.String(length=20), nullable=True),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_recipient_created",
        "notifications",
        ["recipient_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_recipient_id",
        "notifications",
        ["recipient_id"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_recipient_read",
        "notifications",
        ["recipient_id", "is_read"],
        unique=False,
    )

    # JWT 吊销：jti 即主键，存在即视为已吊销
    op.create_table(
        "jwt_blocklist",
        sa.Column("jti", sa.String(length=36), nullable=False),
        sa.Column("token_type", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("jti"),
    )
    op.create_index(
        "ix_jwt_blocklist_user_id",
        "jwt_blocklist",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_jwt_blocklist_user_id", table_name="jwt_blocklist")
    op.drop_table("jwt_blocklist")

    op.drop_index("ix_notifications_recipient_read", table_name="notifications")
    op.drop_index("ix_notifications_recipient_id", table_name="notifications")
    op.drop_index("ix_notifications_recipient_created", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index(
        "ix_email_verification_codes_email_purpose",
        table_name="email_verification_codes",
    )
    op.drop_table("email_verification_codes")
