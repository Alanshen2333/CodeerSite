import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import TSVECTOR

from app.extensions import db


class SearchDocument(db.Model):
    """全文搜索文档表 — 替代 MongoDB search_index 集合。

    字段与业务实体分离，索引写入与业务数据在同一 PG 事务中。
    search_vector 为 tsvector，配合 GIN 索引实现英文/拼音/混合搜索；
    中文子串搜索依赖 pg_trgm 的 GIN 索引（ILIKE + gin_trgm_ops）。
    """

    __tablename__ = "search_documents"
    __table_args__ = (
        db.UniqueConstraint("doc_id", "source_type", name="uq_search_documents_doc_source"),
        # GIN 索引：tsvector 全文搜索
        db.Index("ix_search_documents_search_vector", "search_vector", postgresql_using="gin"),
        # GIN 索引：pg_trgm 支持 ILIKE 中文子串匹配
        db.Index("ix_search_documents_title_trgm", "title",
                 postgresql_using="gin",
                 postgresql_ops={"title": "gin_trgm_ops"}),
        db.Index("ix_search_documents_body_text_trgm", "body_text",
                 postgresql_using="gin",
                 postgresql_ops={"body_text": "gin_trgm_ops"}),
        # B-tree 索引：按 source_type 筛选
        db.Index("ix_search_documents_source_type", "source_type"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doc_id = db.Column(db.String(36), nullable=False)
    source_type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(500), default="", nullable=False)
    body_text = db.Column(db.Text, default="", nullable=False)
    tags = db.Column(db.JSON, default=list, nullable=False)
    extra = db.Column(db.JSON, default=dict, nullable=False)
    search_vector = db.Column(TSVECTOR, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
