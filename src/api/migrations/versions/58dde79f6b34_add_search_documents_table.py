"""add search_documents table (PG search, replaces MongoDB search_index)

Revision ID: 58dde79f6b34
Revises: b2c3d4e5f6a7
Create Date: 2026-07-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR


# revision identifiers, used by Alembic.
revision: str = '58dde79f6b34'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 启用 pg_trgm 扩展（用于中文子串 ILIKE + gin_trgm_ops）
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # 建表
    op.create_table('search_documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('doc_id', sa.String(length=36), nullable=False),
        sa.Column('source_type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('body_text', sa.Text(), nullable=False, server_default=''),
        sa.Column('tags', sa.JSON(), nullable=False),
        sa.Column('extra', sa.JSON(), nullable=False),
        sa.Column('search_vector', TSVECTOR, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doc_id', 'source_type', name='uq_search_documents_doc_source'),
    )

    # GIN 索引：tsvector 全文搜索
    op.create_index('ix_search_documents_search_vector', 'search_documents',
                    ['search_vector'], postgresql_using='gin')

    # GIN 索引：pg_trgm 支持 ILIKE 中文子串匹配
    op.create_index('ix_search_documents_title_trgm', 'search_documents',
                    ['title'], postgresql_using='gin',
                    postgresql_ops={'title': 'gin_trgm_ops'})
    op.create_index('ix_search_documents_body_text_trgm', 'search_documents',
                    ['body_text'], postgresql_using='gin',
                    postgresql_ops={'body_text': 'gin_trgm_ops'})

    # B-tree 索引：按 source_type 筛选
    op.create_index('ix_search_documents_source_type', 'search_documents',
                    ['source_type'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_search_documents_source_type', table_name='search_documents')
    op.drop_index('ix_search_documents_body_text_trgm', table_name='search_documents',
                  postgresql_using='gin')
    op.drop_index('ix_search_documents_title_trgm', table_name='search_documents',
                  postgresql_using='gin')
    op.drop_index('ix_search_documents_search_vector', table_name='search_documents',
                  postgresql_using='gin')
    op.drop_table('search_documents')
    # 不删除 pg_trgm 扩展（downgrade 不删扩展）
