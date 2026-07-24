"""集成测试：搜索功能（PostgreSQL 全文搜索迁移后）。

覆盖：
1. 英文关键词命中 question
2. 中文子串命中（标题/正文）
3. 更新 question 标题后新词可搜、旧词搜不到
4. 删除 question 后搜不到
5. source_type 过滤（question / issue / project）
6. 不传 q（或空 q）按 created_at 倒序返回
7. 分页正确
8. issue / project / answer 删除后搜不到
9. 特殊字符健壮性
"""

import pytest


# ── 辅助函数 ──────────────────────────────────────────────

def _login(client, username, email):
    client.post("/api/auth/register", json={
        "username": username, "email": email, "password": "password123",
    })
    resp = client.post("/api/auth/login", json={
        "email": email, "password": "password123",
    })
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def _create_project(client, headers, name="Search Test Project"):
    resp = client.post(
        "/api/projects",
        json={"name": name, "visibility": "public"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["project"]


def _create_issue(client, headers, slug, title, body=None):
    payload = {"title": title}
    if body:
        payload["body"] = body
    resp = client.post(
        f"/api/projects/{slug}/issues",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["issue"]


def _create_question(client, headers, title, body="Default body text for search tests.", tag_ids=None):
    payload = {"title": title, "body": body}
    if tag_ids:
        payload["tag_ids"] = tag_ids
    resp = client.post("/api/questions", json=payload, headers=headers)
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["question"]


def _search(client, q="", source_type=None, page=1, per_page=20):
    params = {}
    if q is not None:
        params["q"] = q
    if source_type:
        params["type"] = source_type
    if page != 1:
        params["page"] = page
    if per_page != 20:
        params["per_page"] = per_page
    resp = client.get("/api/search", query_string=params)
    return resp


# ── 测试类 ────────────────────────────────────────────────

@pytest.mark.usefixtures("auth_headers")
class TestSearch:
    """搜索基础功能测试。"""

    def test_english_keyword_search(self, client, auth_headers):
        """创建 question 后，英文关键词可搜到；断言 item 字段结构与值。"""
        q = _create_question(
            client, auth_headers,
            title="How to deploy Flask on AWS?",
            body="I need help with Flask deployment.",
        )

        resp = _search(client, q="deploy Flask AWS")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1
        assert data["page"] == 1

        # 找到刚创建的 question
        items = [it for it in data["items"] if it["doc_id"] == q["id"]]
        assert len(items) == 1
        item = items[0]
        assert item["source_type"] == "question"
        assert item["title"] == "How to deploy Flask on AWS?"
        assert isinstance(item["body_text"], str)
        assert len(item["body_text"]) <= 200
        assert item["tags"] == []
        assert "author_name" in item["extra"]
        assert item["extra"]["author_name"] is not None
        assert item["created_at"] is not None

    def test_chinese_substring_title(self, client, auth_headers):
        """中文子串命中：标题含中文的 question，搜其中连续子串能命中。"""
        _create_question(
            client, auth_headers,
            title="如何部署 Flask 应用到生产环境",
            body="本文介绍部署步骤。详细说明如何配置。",
        )
        resp = _search(client, q="部署 Flask")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_chinese_substring_body(self, client, auth_headers):
        """正文里的中文子串也能命中。"""
        _create_question(
            client, auth_headers,
            title="Some English Title",
            body="这里是一段中文正文，包含了关键词。",
        )
        resp = _search(client, q="中文正文")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_update_question_reindex(self, client, auth_headers):
        """更新 question 标题后：新词可搜到，旧标题的词搜不到（验证同事务更新）。"""
        q = _create_question(
            client, auth_headers,
            title="Old Flask Title",
        )
        q_id = q["id"]

        # 旧词应能搜到
        resp = _search(client, q="Old Flask")
        assert resp.status_code == 200
        old_items = [it for it in resp.get_json()["items"] if it["doc_id"] == q_id]
        assert len(old_items) == 1

        # 更新标题
        resp = client.patch(
            f"/api/questions/{q_id}",
            json={"title": "New Django Title"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # 新词应能搜到
        resp = _search(client, q="New Django")
        assert resp.status_code == 200
        new_items = [it for it in resp.get_json()["items"] if it["doc_id"] == q_id]
        assert len(new_items) == 1

        # 旧标题的词应搜不到（或至少搜不到这个 question）
        resp = _search(client, q="Old Flask")
        assert resp.status_code == 200
        old_items_after = [it for it in resp.get_json()["items"] if it["doc_id"] == q_id]
        assert len(old_items_after) == 0

    def test_delete_question_removes_from_search(self, client, auth_headers):
        """删除 question 后搜不到。"""
        q = _create_question(
            client, auth_headers,
            title="Temporary Question",
            body="This will be deleted.",
        )
        q_id = q["id"]

        # 删除前能搜到
        resp = _search(client, q="Temporary Question")
        assert any(it["doc_id"] == q_id for it in resp.get_json()["items"])

        # 删除
        resp = client.delete(f"/api/questions/{q_id}", headers=auth_headers)
        assert resp.status_code == 200

        # 删除后搜不到
        resp = _search(client, q="Temporary Question")
        assert not any(it["doc_id"] == q_id for it in resp.get_json()["items"])

    def test_source_type_filter(self, client, auth_headers):
        """source_type 过滤：各建 question / issue / project，搜共同关键词加 type=question 只返回 question。"""
        shared_keyword = "UnicornSearchTest"

        # Question
        _create_question(
            client, auth_headers,
            title=f"{shared_keyword} Question",
        )
        # Project
        p = _create_project(client, auth_headers, name=f"{shared_keyword} Project")
        # Issue
        _create_issue(client, auth_headers, p["slug"], title=f"{shared_keyword} Issue")

        # 不加类型过滤应返回全部 3 个
        resp = _search(client, q=shared_keyword)
        assert resp.status_code == 200
        assert resp.get_json()["total"] >= 3

        # 加 type=question 只返回 question
        resp = _search(client, q=shared_keyword, source_type="question")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["source_type"] == "question"

        # 加 type=issue 只返回 issue
        resp = _search(client, q=shared_keyword, source_type="issue")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["source_type"] == "issue"

        # 加 type=project 只返回 project
        resp = _search(client, q=shared_keyword, source_type="project")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["source_type"] == "project"

    def test_invalid_source_type_ignored(self, client, auth_headers):
        """非法 source_type 值被忽略（返回全部类型）。"""
        _create_question(client, auth_headers, title="InvalidTypeTest")

        resp = _search(client, q="InvalidTypeTest", source_type="nonexistent")
        assert resp.status_code == 200
        # 非法 type 被忽略，应返回全部（至少 1 条）
        assert resp.get_json()["total"] >= 1

    def test_empty_q_returns_all(self, client, auth_headers):
        """不传 q（或空 q）按 created_at 倒序返回，total 正确。"""
        # 先确保至少有几个文档
        _create_question(client, auth_headers, title="Empty Q Test A")
        _create_question(client, auth_headers, title="Empty Q Test B")

        # 不传 q 参数
        resp = client.get("/api/search")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 2
        assert data["page"] == 1
        assert data["pages"] >= 1
        assert len(data["items"]) >= 1
        # 验证按 created_at 倒序
        if len(data["items"]) >= 2:
            assert data["items"][0]["created_at"] >= data["items"][1]["created_at"]

    def test_pagination(self, client, auth_headers):
        """分页：per_page=1 时 pages 与 total 正确。"""
        # 创建至少 3 个文档
        _create_question(client, auth_headers, title="Pagination Test Alpha")
        _create_question(client, auth_headers, title="Pagination Test Beta")
        _create_question(client, auth_headers, title="Pagination Test Gamma")

        resp = _search(client, q="Pagination Test", per_page=1, page=1)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 3
        assert data["pages"] == data["total"]  # per_page=1 时 pages == total
        assert len(data["items"]) == 1

        # 第 2 页
        resp = _search(client, q="Pagination Test", per_page=1, page=2)
        assert resp.status_code == 200
        data2 = resp.get_json()
        assert len(data2["items"]) == 1
        # 第 1 页和第 2 页的 item 不同
        assert data["items"][0]["doc_id"] != data2["items"][0]["doc_id"]

    def test_issue_delete_removes_from_search(self, client, auth_headers):
        """issue 删除后搜不到。"""
        p = _create_project(client, auth_headers, name="IssueDelProj")
        issue = _create_issue(
            client, auth_headers, p["slug"],
            title="IssueToDelete",
            body="This issue will be removed.",
        )

        # 搜到
        resp = _search(client, q="IssueToDelete")
        assert any(it["doc_id"] == issue["id"] for it in resp.get_json()["items"])

        # 删除 issue
        resp = client.delete(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # 搜不到
        resp = _search(client, q="IssueToDelete")
        assert not any(it["doc_id"] == issue["id"] for it in resp.get_json()["items"])

    def test_project_delete_removes_from_search(self, client, auth_headers):
        """project 删除后搜不到。"""
        p = _create_project(client, auth_headers, name="ProjectToDelete")
        p_id = p["id"]

        # 搜到
        resp = _search(client, q="ProjectToDelete")
        assert any(it["doc_id"] == p_id for it in resp.get_json()["items"])

        # 删除 project
        resp = client.delete(f"/api/projects/{p['slug']}", headers=auth_headers)
        assert resp.status_code == 200

        # 搜不到
        resp = _search(client, q="ProjectToDelete")
        assert not any(it["doc_id"] == p_id for it in resp.get_json()["items"])

    def test_answer_searchable(self, client, auth_headers):
        """answer 创建后可通过其正文关键词搜到。"""
        q = _create_question(
            client, auth_headers,
            title="Answer Search Test",
            body="Parent question body.",
        )

        # 创建 answer
        resp = client.post("/api/answers", json={
            "question_id": q["id"],
            "body": "This is a unique answer body for search testing.",
        }, headers=auth_headers)
        assert resp.status_code == 201
        answer = resp.get_json()["answer"]

        # 搜索 answer 正文关键词
        resp = _search(client, q="unique answer body")
        assert resp.status_code == 200
        data = resp.get_json()
        answer_items = [it for it in data["items"] if it["doc_id"] == answer["id"]]
        assert len(answer_items) >= 1
        assert answer_items[0]["source_type"] == "answer"

    def test_answer_delete_removes_from_search(self, client, auth_headers):
        """answer 删除后搜不到。"""
        q = _create_question(
            client, auth_headers,
            title="Answer Delete Test",
            body="Parent body.",
        )
        resp = client.post("/api/answers", json={
            "question_id": q["id"],
            "body": "Answer to be deleted for search test.",
        }, headers=auth_headers)
        assert resp.status_code == 201
        answer = resp.get_json()["answer"]

        # 删除前能搜到
        resp = _search(client, q="Answer to be deleted")
        assert any(it["doc_id"] == answer["id"] for it in resp.get_json()["items"])

        # 删除 answer
        resp = client.delete(f"/api/answers/{answer['id']}", headers=auth_headers)
        assert resp.status_code == 200

        # 删除后搜不到
        resp = _search(client, q="Answer to be deleted")
        assert not any(it["doc_id"] == answer["id"] for it in resp.get_json()["items"])

    def test_special_characters_percent(self, client, auth_headers):
        """q 含 '100%' 时不报错、返回正常结构。"""
        _create_question(client, auth_headers, title="Special 100% char test")
        resp = _search(client, q="100%")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data

    def test_special_characters_underscore(self, client, auth_headers):
        """q 含 'a_b' 时不报错、返回正常结构。"""
        _create_question(client, auth_headers, title="Special a_b char test")
        resp = _search(client, q="a_b")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
