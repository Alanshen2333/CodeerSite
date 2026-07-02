from typing import Optional
import mistune
from app.extensions import db
from app.models.issue import Issue, TimeEntry
from app.models.project import Project
from app.models.tag import Tag
from app.services.search_service import SearchService
from app.services.notification_service import NotificationService

_md_renderer = mistune.create_markdown(escape=True, hard_wrap=True)


class IssueService:
    @staticmethod
    def create_issue(
        project_id: str, author_id: str, title: str,
        body: str = None, assignee_id: str = None,
        priority: str = "medium", milestone_id: str = None,
        tag_ids: list = None, time_estimate: int = None,
    ) -> Issue:
        # Generate next issue_number for this project
        max_num = (
            db.session.query(db.func.max(Issue.issue_number))
            .filter_by(project_id=project_id)
            .scalar()
        ) or 0

        body_html = _md_renderer(body) if body else None

        issue = Issue(
            project_id=project_id,
            issue_number=max_num + 1,
            title=title.strip(),
            body=body,
            body_html=body_html,
            author_id=author_id,
            assignee_id=assignee_id,
            priority=priority,
            milestone_id=milestone_id,
            time_estimate=time_estimate,
        )
        db.session.add(issue)
        db.session.commit()
        IssueService._index_to_search(issue)

        # 关联标签（复用全局 Tag，多对多）
        if tag_ids:
            issue.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            db.session.commit()

        # Notify assignee if one was set
        if assignee_id and assignee_id != author_id:
            from app.models.user import User
            project = db.session.get(Project, project_id)
            project_slug = project.slug if project else ""
            assignee = db.session.get(User, assignee_id)
            NotificationService.create(
                recipient_id=assignee_id,
                type_="issue_assigned",
                title=f"{assignee.display_name or '你'} 被分配到 Issue #{issue.issue_number}",
                body=title[:200],
                link=f"/projects/{project_slug}/issues/{issue.issue_number}",
                source_type="issue",
                source_id=issue.id,
            )

        return issue

    @staticmethod
    def update_issue(issue: Issue, **kwargs) -> Issue:
        old_assignee_id = issue.assignee_id
        for field in ("title", "body", "assignee_id", "status", "priority",
                      "milestone_id", "time_estimate"):
            if field in kwargs and kwargs[field] is not None or field in kwargs:
                setattr(issue, field, kwargs[field])

        if "body" in kwargs and kwargs["body"] is not None:
            issue.body_html = _md_renderer(kwargs["body"])

        # 标签更新（整体替换；空列表清空）
        if "tag_ids" in kwargs:
            tag_ids = kwargs.get("tag_ids")
            issue.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all() if tag_ids else []

        db.session.commit()
        IssueService._index_to_search(issue)

        # Notify new assignee if changed
        new_assignee = kwargs.get("assignee_id")
        if new_assignee and new_assignee != old_assignee_id:
            project = db.session.get(Project, issue.project_id)
            slug = project.slug if project else ""
            NotificationService.create(
                recipient_id=new_assignee,
                type_="issue_assigned",
                title=f"你被分配到 Issue #{issue.issue_number}",
                body=issue.title[:200],
                link=f"/projects/{slug}/issues/{issue.issue_number}",
                source_type="issue",
                source_id=issue.id,
            )

        return issue

    @staticmethod
    def delete_issue(issue: Issue):
        IssueService._remove_from_search(issue)
        db.session.delete(issue)
        db.session.commit()

    @staticmethod
    def get_issue(issue_id: str = None, project_id: str = None, issue_number: int = None) -> Optional[Issue]:
        if issue_id:
            return db.session.get(Issue, issue_id)
        if project_id and issue_number:
            return Issue.query.filter_by(project_id=project_id, issue_number=issue_number).first()
        return None

    @staticmethod
    def get_issues(
        project_id: str,
        page: int = 1, per_page: int = 20,
        status: str = None, priority: str = None,
        assignee_id: str = None, milestone_id: str = None,
        tag_id: str = None, sort: str = "newest",
    ):
        query = Issue.query.filter_by(project_id=project_id)

        if status:
            query = query.filter_by(status=status)
        if priority:
            query = query.filter_by(priority=priority)
        if assignee_id:
            query = query.filter_by(assignee_id=assignee_id)
        if milestone_id is not None:
            query = query.filter_by(milestone_id=milestone_id)
        if tag_id:
            query = query.join(Issue.tags).filter(Tag.id == tag_id)

        if sort == "oldest":
            query = query.order_by(Issue.created_at.asc())
        elif sort == "priority":
            query = query.order_by(
                db.case(
                    {"critical": 0, "high": 1, "medium": 2, "low": 3},
                    value=Issue.priority,
                ),
                Issue.created_at.desc(),
            )
        else:  # newest
            query = query.order_by(Issue.created_at.desc())

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_issue_stats(project_id: str) -> dict:
        """Get issue counts by status."""
        open_count = Issue.query.filter_by(project_id=project_id, status="open").count()
        in_progress = Issue.query.filter_by(project_id=project_id, status="in_progress").count()
        closed = Issue.query.filter_by(project_id=project_id, status="closed").count()
        return {"open": open_count, "in_progress": in_progress, "closed": closed, "total": open_count + in_progress + closed}

    @staticmethod
    def _index_to_search(issue: Issue):
        SearchService.index_document(
            doc_id=issue.id,
            source_type="issue",
            title=issue.title,
            body_text=(issue.body or "")[:1000],
            created_at=issue.created_at,
            extra={"issue_number": issue.issue_number, "project_id": issue.project_id,
                   "status": issue.status, "author_name": issue.author.display_name if issue.author else None},
        )

    @staticmethod
    def _remove_from_search(issue: Issue):
        SearchService.remove_document(issue.id, "issue")

    # ── 时间跟踪 ──────────────────────────────────────────

    @staticmethod
    def add_time_entry(issue: Issue, user_id: str, seconds: int,
                       note: str = None) -> TimeEntry:
        """记录一段耗时：创建 TimeEntry 并同步累加 Issue.time_spent 反范式缓存。"""
        entry = TimeEntry(
            issue_id=issue.id,
            user_id=user_id,
            seconds=seconds,
            note=note,
        )
        db.session.add(entry)
        issue.time_spent = (issue.time_spent or 0) + seconds
        db.session.commit()
        return entry

    @staticmethod
    def get_time_entries(issue: Issue) -> list[TimeEntry]:
        """返回某 Issue 的全部耗时条目（按时间倒序）。"""
        return (
            TimeEntry.query
            .filter_by(issue_id=issue.id)
            .order_by(TimeEntry.created_at.desc())
            .all()
        )
