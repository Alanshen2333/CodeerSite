"""add milestone issue count cache columns

Revision ID: f9a1b2c3d4e5
Revises: 7f765b14d7e5
Create Date: 2026-07-13 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f9a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "7f765b14d7e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "milestones",
        sa.Column(
            "open_issues_count", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "milestones",
        sa.Column(
            "closed_issues_count", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    # 用 SQL 回填现有 milestone 的计数
    op.execute("""
        UPDATE milestones SET
            open_issues_count = (
                SELECT COUNT(*) FROM issues
                WHERE issues.milestone_id = milestones.id AND issues.status != 'closed'
            ),
            closed_issues_count = (
                SELECT COUNT(*) FROM issues
                WHERE issues.milestone_id = milestones.id AND issues.status = 'closed'
            )
    """)


def downgrade() -> None:
    op.drop_column("milestones", "closed_issues_count")
    op.drop_column("milestones", "open_issues_count")
