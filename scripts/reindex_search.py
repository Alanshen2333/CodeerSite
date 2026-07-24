"""搜索索引回填脚本 — 从 PG 主数据重建 search_documents 表。

用途：搜索从 MongoDB 迁到 PostgreSQL 后，存量业务数据没有对应索引记录，
运行本脚本全量重建（幂等，可重复执行）。

用法：
    FLASK_ENV=development uv run python scripts/reindex_search.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "api"))

from app import create_app
from app.extensions import db
from app.models.answer import Answer
from app.models.issue import Issue
from app.models.project import Project
from app.models.question import Question
from app.models.search_document import SearchDocument
from app.services.answer_service import AnswerService
from app.services.issue_service import IssueService
from app.services.project_service import ProjectService
from app.services.question_service import QuestionService


def main() -> None:
    app = create_app()
    with app.app_context():
        # 清空旧索引，整体重建（幂等）
        SearchDocument.query.delete()

        counts = {}
        for model, service, name in [
            (Question, QuestionService, "question"),
            (Answer, AnswerService, "answer"),
            (Issue, IssueService, "issue"),
            (Project, ProjectService, "project"),
        ]:
            rows = model.query.all()
            for row in rows:
                if name == "answer":
                    # 与线上路径一致：标题取所属问题标题
                    service._index_to_search(row, row.question)
                else:
                    service._index_to_search(row)
            counts[name] = len(rows)

        db.session.commit()
        summary = ", ".join(f"{k}={v}" for k, v in counts.items())
        print(f"重建完成：{summary}")


if __name__ == "__main__":
    main()
