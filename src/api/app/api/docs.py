from flask import Blueprint, jsonify, current_app

docs_bp = Blueprint("docs", __name__)


@docs_bp.route("/docs", methods=["GET"])
def api_docs():
    """Return OpenAPI 3.0 spec for all API endpoints."""
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Codeersite API",
            "version": "0.1.0",
            "description": "开发者社区平台 REST API",
        },
        "servers": [{"url": "/api", "description": "API 基础路径"}],
        "tags": [
            {"name": "Auth", "description": "认证"},
            {"name": "Users", "description": "用户"},
            {"name": "Questions", "description": "问题"},
            {"name": "Answers", "description": "回答"},
            {"name": "Votes", "description": "投票"},
            {"name": "Comments", "description": "评论"},
            {"name": "Tags", "description": "标签"},
            {"name": "Bookmarks", "description": "收藏"},
            {"name": "Projects", "description": "项目"},
            {"name": "Issues", "description": "Issue 管理"},
            {"name": "Milestones", "description": "里程碑"},
            {"name": "Kanban", "description": "看板"},
            {"name": "Search", "description": "搜索"},
            {"name": "Notifications", "description": "通知"},
            {"name": "Admin", "description": "管理员"},
        ],
        "paths": {
            "/auth/register": {
                "post": {"tags": ["Auth"], "summary": "注册", "security": []}
            },
            "/auth/login": {
                "post": {"tags": ["Auth"], "summary": "登录", "security": []}
            },
            "/auth/refresh": {
                "post": {"tags": ["Auth"], "summary": "刷新 Token"}
            },
            "/auth/me": {
                "get": {"tags": ["Auth"], "summary": "获取当前用户"},
                "patch": {"tags": ["Auth"], "summary": "更新个人资料"},
            },
            "/users": {
                "get": {"tags": ["Users"], "summary": "用户列表（按声望排序）", "security": []}
            },
            "/users/{username}": {
                "get": {"tags": ["Users"], "summary": "用户详情 + 统计 + 成就", "security": []}
            },
            "/users/{username}/questions": {
                "get": {"tags": ["Users"], "summary": "用户的问题列表", "security": []}
            },
            "/users/{username}/answers": {
                "get": {"tags": ["Users"], "summary": "用户的回答列表", "security": []}
            },
            "/questions": {
                "get": {"tags": ["Questions"], "summary": "问题列表（分页/排序/筛选）", "security": []},
                "post": {"tags": ["Questions"], "summary": "创建问题"},
            },
            "/questions/{id}": {
                "get": {"tags": ["Questions"], "summary": "问题详情（增加浏览数）", "security": []},
                "patch": {"tags": ["Questions"], "summary": "编辑问题"},
                "delete": {"tags": ["Questions"], "summary": "删除问题"},
            },
            "/questions/{id}/close": {
                "post": {"tags": ["Questions"], "summary": "关闭问题"},
            },
            "/questions/{id}/reopen": {
                "post": {"tags": ["Questions"], "summary": "打开问题"},
            },
            "/questions/{id}/pin": {
                "post": {"tags": ["Questions"], "summary": "切换置顶（管理员/版主）"},
            },
            "/answers": {
                "get": {"tags": ["Answers"], "summary": "回答列表", "security": []},
                "post": {"tags": ["Answers"], "summary": "创建回答"},
            },
            "/answers/{id}": {
                "patch": {"tags": ["Answers"], "summary": "编辑回答"},
                "delete": {"tags": ["Answers"], "summary": "删除回答"},
            },
            "/answers/{id}/accept": {
                "post": {"tags": ["Answers"], "summary": "采纳回答（问题作者）"},
                "delete": {"tags": ["Answers"], "summary": "取消采纳"},
            },
            "/votes": {
                "post": {"tags": ["Votes"], "summary": "投票（赞/踩）"},
                "delete": {"tags": ["Votes"], "summary": "取消投票"},
            },
            "/comments": {
                "get": {"tags": ["Comments"], "summary": "评论列表", "security": []},
                "post": {"tags": ["Comments"], "summary": "创建评论"},
            },
            "/comments/{id}": {
                "patch": {"tags": ["Comments"], "summary": "编辑评论"},
                "delete": {"tags": ["Comments"], "summary": "删除评论"},
            },
            "/tags": {
                "get": {"tags": ["Tags"], "summary": "标签列表", "security": []},
                "post": {"tags": ["Tags"], "summary": "创建标签"},
            },
            "/tags/{slug}": {
                "get": {"tags": ["Tags"], "summary": "标签详情", "security": []}
            },
            "/bookmarks": {
                "get": {"tags": ["Bookmarks"], "summary": "收藏列表"},
                "post": {"tags": ["Bookmarks"], "summary": "切换收藏"},
            },
            "/bookmarks/check": {
                "get": {"tags": ["Bookmarks"], "summary": "检查是否已收藏"},
            },
            "/projects": {
                "get": {"tags": ["Projects"], "summary": "项目列表", "security": []},
                "post": {"tags": ["Projects"], "summary": "创建项目"},
            },
            "/projects/{slug}": {
                "get": {"tags": ["Projects"], "summary": "项目详情", "security": []},
                "patch": {"tags": ["Projects"], "summary": "编辑项目"},
                "delete": {"tags": ["Projects"], "summary": "删除项目"},
            },
            "/projects/{slug}/members": {
                "get": {"tags": ["Projects"], "summary": "成员列表", "security": []},
                "post": {"tags": ["Projects"], "summary": "添加成员"},
            },
            "/projects/{slug}/members/{user_id}": {
                "patch": {"tags": ["Projects"], "summary": "更新成员角色"},
                "delete": {"tags": ["Projects"], "summary": "移除成员"},
            },
            "/projects/{slug}/star": {
                "post": {"tags": ["Projects"], "summary": "Star 项目"},
            },
            "/projects/{slug}/issues": {
                "get": {"tags": ["Issues"], "summary": "Issue 列表", "security": []},
                "post": {"tags": ["Issues"], "summary": "创建 Issue"},
            },
            "/projects/{slug}/issues/{issue_number}": {
                "get": {"tags": ["Issues"], "summary": "Issue 详情", "security": []},
                "patch": {"tags": ["Issues"], "summary": "编辑 Issue"},
                "delete": {"tags": ["Issues"], "summary": "删除 Issue"},
            },
            "/projects/{slug}/milestones": {
                "get": {"tags": ["Milestones"], "summary": "里程碑列表", "security": []},
                "post": {"tags": ["Milestones"], "summary": "创建里程碑"},
            },
            "/projects/{slug}/milestones/{id}": {
                "patch": {"tags": ["Milestones"], "summary": "编辑里程碑"},
                "delete": {"tags": ["Milestones"], "summary": "删除里程碑"},
            },
            "/projects/{slug}/kanban/columns": {
                "get": {"tags": ["Kanban"], "summary": "看板列列表", "security": []},
                "post": {"tags": ["Kanban"], "summary": "创建看板列"},
            },
            "/projects/{slug}/kanban/columns/{id}": {
                "patch": {"tags": ["Kanban"], "summary": "编辑看板列"},
                "delete": {"tags": ["Kanban"], "summary": "删除看板列"},
            },
            "/projects/{slug}/kanban/columns/reorder": {
                "post": {"tags": ["Kanban"], "summary": "列排序"},
            },
            "/projects/{slug}/kanban/columns/{id}/cards": {
                "post": {"tags": ["Kanban"], "summary": "创建看板卡片"},
            },
            "/projects/{slug}/kanban/cards/{id}": {
                "patch": {"tags": ["Kanban"], "summary": "编辑卡片"},
                "delete": {"tags": ["Kanban"], "summary": "删除卡片"},
            },
            "/projects/{slug}/kanban/cards/{id}/move": {
                "post": {"tags": ["Kanban"], "summary": "移动卡片"},
            },
            "/search": {
                "get": {"tags": ["Search"], "summary": "全文搜索", "security": []}
            },
            "/notifications": {
                "get": {"tags": ["Notifications"], "summary": "通知列表"},
                "patch": {"tags": ["Notifications"], "summary": "全部已读（/read-all）"},
            },
            "/notifications/unread-count": {
                "get": {"tags": ["Notifications"], "summary": "未读通知数"},
            },
            "/notifications/{id}/read": {
                "patch": {"tags": ["Notifications"], "summary": "标记单条已读"},
            },
            "/admin/stats": {
                "get": {"tags": ["Admin"], "summary": "站点统计（管理员）"},
            },
            "/admin/users": {
                "get": {"tags": ["Admin"], "summary": "用户列表（管理员）"},
            },
            "/admin/users/{id}": {
                "patch": {"tags": ["Admin"], "summary": "编辑用户（管理员）"},
                "delete": {"tags": ["Admin"], "summary": "删除用户（管理员）"},
            },
        },
    }
    return jsonify(spec), 200
