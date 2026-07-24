"""add issue counter and nonnegative check constraints

Revision ID: 7f765b14d7e5
Revises: afd247718c46
Create Date: 2026-07-07 10:49:42.612250

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f765b14d7e5"
down_revision: Union[str, Sequence[str], None] = "afd247718c46"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 新增 projects.next_issue_number，先允许 NULL 以便后续初始化
    op.add_column(
        "projects",
        sa.Column("next_issue_number", sa.Integer(), nullable=True),
    )

    # 2. 迁移前清理所有负值计数，避免 CHECK 约束创建失败
    op.execute("UPDATE users SET reputation = GREATEST(reputation, 0)")
    op.execute("UPDATE questions SET vote_count = GREATEST(vote_count, 0)")
    op.execute("UPDATE questions SET answer_count = GREATEST(answer_count, 0)")
    op.execute("UPDATE questions SET view_count = GREATEST(view_count, 0)")
    op.execute("UPDATE answers SET vote_count = GREATEST(vote_count, 0)")
    op.execute("UPDATE projects SET star_count = GREATEST(star_count, 0)")

    # 3. 根据现有 issue 初始化 next_issue_number
    op.execute(
        """
        UPDATE projects
        SET next_issue_number = COALESCE(
            (SELECT MAX(issue_number) FROM issues WHERE issues.project_id = projects.id),
            0
        ) + 1
        """
    )

    # 4. 设置默认值并改为非空
    op.alter_column(
        "projects",
        "next_issue_number",
        existing_type=sa.Integer(),
        nullable=False,
        server_default="1",
    )

    # 5. 添加 CHECK 约束
    op.create_check_constraint(
        "ck_projects_star_count_nonnegative",
        "projects",
        "star_count >= 0",
    )
    op.create_check_constraint(
        "ck_projects_next_issue_number_positive",
        "projects",
        "next_issue_number >= 1",
    )
    op.create_check_constraint(
        "ck_users_reputation_nonnegative",
        "users",
        "reputation >= 0",
    )
    op.create_check_constraint(
        "ck_questions_vote_count_nonnegative",
        "questions",
        "vote_count >= 0",
    )
    op.create_check_constraint(
        "ck_questions_answer_count_nonnegative",
        "questions",
        "answer_count >= 0",
    )
    op.create_check_constraint(
        "ck_questions_view_count_nonnegative",
        "questions",
        "view_count >= 0",
    )
    op.create_check_constraint(
        "ck_answers_vote_count_nonnegative",
        "answers",
        "vote_count >= 0",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_answers_vote_count_nonnegative", "answers", type_="check")
    op.drop_constraint(
        "ck_questions_view_count_nonnegative", "questions", type_="check"
    )
    op.drop_constraint(
        "ck_questions_answer_count_nonnegative", "questions", type_="check"
    )
    op.drop_constraint(
        "ck_questions_vote_count_nonnegative", "questions", type_="check"
    )
    op.drop_constraint("ck_users_reputation_nonnegative", "users", type_="check")
    op.drop_constraint(
        "ck_projects_next_issue_number_positive", "projects", type_="check"
    )
    op.drop_constraint("ck_projects_star_count_nonnegative", "projects", type_="check")

    op.alter_column(
        "projects",
        "next_issue_number",
        existing_type=sa.Integer(),
        nullable=True,
        server_default=None,
    )
    op.drop_column("projects", "next_issue_number")
