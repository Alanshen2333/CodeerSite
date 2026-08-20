import logging
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, literal_column, select

from app.extensions import db
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.search_document import SearchDocument

logger = logging.getLogger(__name__)

# tsvector 配置：必须用 regconfig 字面量。
# 直接传字符串会被 psycopg 绑成 VARCHAR 参数，PG 无法解析
# plainto_tsquery(varchar, varchar)（varchar→regconfig 非隐式转换）。
_SIMPLE_CFG = literal_column("'simple'::regconfig")


class SearchService:
    """PostgreSQL 全文搜索 — 替代 MongoDB search_index 集合。

    使用 tsvector + pg_trgm 实现混合搜索：
    - tsvector 支持英文/拼音/混合搜索（setweight 分层：标题 A > 标签 B > 正文 C）
    - pg_trgm ILIKE 兜底中文子串（tsvector 对中文分词无效，中文命中靠 ILIKE）
    """

    INDEXED_TYPES = ("question", "answer", "issue", "project")

    @staticmethod
    def _escape_ilike(s: str) -> str:
        """转义 ILIKE 通配符 % _ \\，防止用户输入干扰模式匹配。"""
        return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    @staticmethod
    def index_document(
        doc_id: str,
        source_type: str,
        title: str,
        body_text: str,
        tags: list[str] | None = None,
        created_at: datetime | None = None,
        extra: dict | None = None,
    ):
        """索引/更新文档。只 flush 不 commit，由调用方事务统一提交。"""
        # 查找已有记录
        doc = SearchDocument.query.filter_by(
            doc_id=doc_id, source_type=source_type
        ).first()

        if created_at is None:
            created_at = datetime.now(timezone.utc)

        if doc:
            doc.title = title or ""
            doc.body_text = body_text or ""
            doc.tags = tags or []
            doc.extra = extra or {}
            doc.created_at = created_at
        else:
            doc = SearchDocument(
                doc_id=doc_id,
                source_type=source_type,
                title=title or "",
                body_text=body_text or "",
                tags=tags or [],
                extra=extra or {},
                created_at=created_at,
            )
            db.session.add(doc)

        # 构造 tsvector：title(A) || tags(B) || body_text(C)
        # setweight 第二参数必须为 PostgreSQL "char" 类型，literal_column 避免被绑为 varchar
        tag_text = " ".join(tags or [])
        doc.search_vector = (
            func.setweight(
                func.to_tsvector(_SIMPLE_CFG, func.coalesce(title or "", "")),
                literal_column("'A'::\"char\""),
            )
            .op("||")(
                func.setweight(
                    func.to_tsvector(_SIMPLE_CFG, func.coalesce(tag_text, "")),
                    literal_column("'B'::\"char\""),
                )
            )
            .op("||")(
                func.setweight(
                    func.to_tsvector(_SIMPLE_CFG, func.coalesce(body_text or "", "")),
                    literal_column("'C'::\"char\""),
                )
            )
        )

        db.session.flush()

    @staticmethod
    def remove_document(doc_id: str, source_type: str):
        """从索引中移除文档。不 commit，由调用方事务统一提交。"""
        doc = SearchDocument.query.filter_by(
            doc_id=doc_id, source_type=source_type
        ).first()
        if doc:
            db.session.delete(doc)
            db.session.flush()

    @staticmethod
    def search(
        q: str,
        source_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
        user_id: str | None = None,
    ) -> dict:
        """全文搜索，返回结构与旧版 MongoDB 实现一致。"""
        empty = {"items": [], "total": 0, "page": page, "pages": 0}

        try:
            query = SearchDocument.query

            visible_project_ids = select(Project.id).where(
                Project.visibility == "public"
            )
            if user_id:
                member_project_ids = select(ProjectMember.project_id).where(
                    ProjectMember.user_id == user_id
                )
                visible_project_ids = select(Project.id).where(
                    or_(
                        Project.visibility == "public",
                        Project.id.in_(member_project_ids),
                    )
                )

            # 问答内容始终公开；项目及其 Issue 必须落在当前用户可见项目集合中。
            query = query.filter(
                or_(
                    SearchDocument.source_type.notin_(("project", "issue")),
                    and_(
                        SearchDocument.source_type == "project",
                        SearchDocument.doc_id.in_(visible_project_ids),
                    ),
                    and_(
                        SearchDocument.source_type == "issue",
                        SearchDocument.extra["project_id"]
                        .as_string()
                        .in_(visible_project_ids),
                    ),
                )
            )

            # source_type 筛选（仅限已知类型，非法值忽略）
            if source_type and source_type in SearchService.INDEXED_TYPES:
                query = query.filter(SearchDocument.source_type == source_type)

            if q:
                q_clean = q.strip()
                escaped = SearchService._escape_ilike(q_clean)

                # 匹配条件：tsvector 全文搜索 OR ILIKE 中文子串兜底
                condition = or_(
                    SearchDocument.search_vector.op("@@")(
                        func.plainto_tsquery(_SIMPLE_CFG, q_clean)
                    ),
                    SearchDocument.title.ilike(f"%{escaped}%", escape="\\"),
                    SearchDocument.body_text.ilike(f"%{escaped}%", escape="\\"),
                )
                query = query.filter(condition)

                # 排序：ts_rank_cd + similarity * 0.3 DESC（让纯中文命中也有相关度），再 created_at DESC
                query = query.order_by(
                    (
                        func.ts_rank_cd(
                            SearchDocument.search_vector,
                            func.plainto_tsquery(_SIMPLE_CFG, q_clean),
                        )
                        + func.similarity(SearchDocument.title, q_clean) * 0.3
                    ).desc(),
                    SearchDocument.created_at.desc(),
                )
            else:
                # 无关键词：按创建时间倒序
                query = query.order_by(SearchDocument.created_at.desc())

            total = query.count()
            rows = query.offset((page - 1) * per_page).limit(per_page).all()

            items = [
                {
                    "doc_id": d.doc_id,
                    "source_type": d.source_type,
                    "title": d.title,
                    "body_text": (d.body_text or "")[:200],
                    "tags": d.tags or [],
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                    "extra": d.extra or {},
                }
                for d in rows
            ]
            pages = (total + per_page - 1) // per_page
            return {"items": items, "total": total, "page": page, "pages": pages}
        except Exception:
            logger.exception("Search error")
            return empty
