"""端到端 Q&A 流程测试：发帖 → 回帖 → 点赞 → 采纳 → 收藏。

直连 Docker compose 起的 PG + Mongo，用 Flask test client 驱动完整 API 流程。
用法：.venv/bin/python scripts/e2e_qa.py
"""

import os
import sys
import uuid
import json
import traceback
from datetime import datetime

# 确保导入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "api"))

from app import create_app
from app.extensions import db

# 用唯一前缀避免数据冲突
RUN_ID = uuid.uuid4().hex[:8]
USER_A = f"alice_{RUN_ID}"
USER_B = f"bob_{RUN_ID}"
EMAIL_A = f"{USER_A}@e2e.test"
EMAIL_B = f"{USER_B}@e2e.test"
PASS = "Test1234!"

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} {detail}")


def main():
    app = create_app("development")
    client = app.test_client()

    print(f"端到端 Q&A 流程测试 (run={RUN_ID})")
    print(f"数据库: {app.config['SQLALCHEMY_DATABASE_URI'][:40]}...")
    print()

    # ── 1. 注册两个用户 ──────────────────────────────
    print("1. 用户注册")
    r = client.post("/api/auth/register", json={
        "username": USER_A, "email": EMAIL_A, "password": PASS,
    })
    check("注册 alice", r.status_code == 201, f"got {r.status_code}: {r.get_data(as_text=True)[:120]}")
    token_a = r.get_json()["access_token"]

    r = client.post("/api/auth/register", json={
        "username": USER_B, "email": EMAIL_B, "password": PASS,
    })
    check("注册 bob", r.status_code == 201, f"got {r.status_code}")
    token_b = r.get_json()["access_token"]

    ha = {"Authorization": f"Bearer {token_a}"}
    hb = {"Authorization": f"Bearer {token_b}"}

    # ── 2. 发帖 ──────────────────────────────────────
    print("2. 发帖（alice 提问）")
    r = client.post("/api/questions", headers=ha, json={
        "title": f"E2E 测试问题 {RUN_ID}",
        "body": "这是一个端到端测试问题，包含 **markdown** 和 `code`。",
        "tag_ids": [],
    })
    check("发帖成功", r.status_code == 201, f"got {r.status_code}: {r.get_data(as_text=True)[:120]}")
    q = r.get_json()["question"]
    qid = q["id"]
    check("body_html 已渲染", "<" in (q.get("body_html") or ""), "html 未生成")
    check("view_count=0", q["view_count"] == 0, f"got {q['view_count']}")
    check("answer_count=0", q["answer_count"] == 0)

    # ── 3. 查看问题（浏览数+1）──────────────────────
    print("3. 查看问题")
    r = client.get(f"/api/questions/{qid}")
    check("详情 200", r.status_code == 200)
    check("view_count=1", r.get_json()["question"]["view_count"] == 1)

    # ── 4. 回帖（bob 回答）──────────────────────────
    print("4. 回帖（bob 回答）")
    r = client.post("/api/answers", headers=hb, json={
        "question_id": qid,
        "body": "这是端到端测试回答。\n\n```python\nprint('hi')\n```",
    })
    check("回帖成功", r.status_code == 201, f"got {r.status_code}: {r.get_data(as_text=True)[:120]}")
    aid = r.get_json()["answer"]["id"]

    r = client.get(f"/api/questions/{qid}")
    check("answer_count=1", r.get_json()["question"]["answer_count"] == 1)

    # ── 5. 点赞 ──────────────────────────────────────
    print("5. 点赞")
    # bob 给问题点赞
    r = client.post("/api/votes", headers=hb, json={
        "vote_type": "up", "target_type": "question", "target_id": qid,
    })
    check("bob 赞问题", r.status_code == 200, f"got {r.status_code}")
    r = client.get(f"/api/questions/{qid}")
    check("问题 vote_count=1", r.get_json()["question"]["vote_count"] == 1)

    # alice 不能给自己的问题点赞
    r = client.post("/api/votes", headers=ha, json={
        "vote_type": "up", "target_type": "question", "target_id": qid,
    })
    check("不能赞自己内容", r.status_code == 400, f"got {r.status_code}")

    # bob 给回答点赞
    r = client.post("/api/votes", headers=hb, json={
        "vote_type": "up", "target_type": "answer", "target_id": aid,
    })
    check("不能赞自己回答", r.status_code == 400, f"got {r.status_code}")

    # alice 给 bob 的回答点赞
    r = client.post("/api/votes", headers=ha, json={
        "vote_type": "up", "target_type": "answer", "target_id": aid,
    })
    check("alice 赞 bob 回答", r.status_code == 200, f"got {r.status_code}")

    # 切换为踩
    r = client.post("/api/votes", headers=ha, json={
        "vote_type": "down", "target_type": "answer", "target_id": aid,
    })
    check("切换为踩", r.status_code == 200, f"got {r.status_code}")

    # 取消投票
    r = client.delete("/api/votes", headers=ha, query_string={
        "target_type": "answer", "target_id": aid,
    })
    check("取消投票", r.status_code == 200, f"got {r.status_code}")

    # ── 6. 采纳 ──────────────────────────────────────
    print("6. 采纳回答")
    # bob 不能采纳（非问题作者）
    r = client.post(f"/api/answers/{aid}/accept", headers=hb)
    check("非作者不能采纳", r.status_code == 403, f"got {r.status_code}")
    # alice 采纳
    r = client.post(f"/api/answers/{aid}/accept", headers=ha)
    check("alice 采纳", r.status_code == 200, f"got {r.status_code}")
    r = client.get("/api/answers", query_string={"question_id": qid})
    check("回答 is_accepted", r.get_json()["answers"][0]["is_accepted"] is True)

    # ── 7. 收藏 ──────────────────────────────────────
    print("7. 收藏")
    # bob 收藏问题
    r = client.post("/api/bookmarks", headers=hb, json={
        "target_type": "question", "target_id": qid,
    })
    check("收藏成功", r.status_code == 201, f"got {r.status_code}: {r.get_data(as_text=True)[:80]}")
    # 再次调用 = 取消收藏
    r = client.post("/api/bookmarks", headers=hb, json={
        "target_type": "question", "target_id": qid,
    })
    check("再次调用=取消", r.status_code == 200, f"got {r.status_code}")
    # 检查未收藏
    r = client.get("/api/bookmarks/check", headers=hb, query_string={
        "target_type": "question", "target_id": qid,
    })
    check("check 返回 false", r.get_json()["bookmarked"] is False)
    # 重新收藏
    client.post("/api/bookmarks", headers=hb, json={
        "target_type": "question", "target_id": qid,
    })
    r = client.get("/api/bookmarks/check", headers=hb, query_string={
        "target_type": "question", "target_id": qid,
    })
    check("check 返回 true", r.get_json()["bookmarked"] is True)
    r = client.get("/api/bookmarks", headers=hb)
    check("收藏列表含1项", r.get_json()["total"] == 1, f"got {r.get_json().get('total')}")

    # ── 8. 评论 ──────────────────────────────────────
    print("8. 评论")
    r = client.post("/api/comments", headers=hb, json={
        "body": "好问题！", "target_type": "question", "target_id": qid,
    })
    check("评论成功", r.status_code == 201, f"got {r.status_code}")
    r = client.get("/api/comments", query_string={
        "target_type": "question", "target_id": qid,
    })
    check("评论数=1", r.get_json()["total"] == 1)

    # ── 9. 删除清理 ──────────────────────────────────
    print("9. 清理")
    r = client.delete(f"/api/questions/{qid}", headers=ha)
    check("删除问题", r.status_code == 200, f"got {r.status_code}")

    print()
    print(f"结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(2)
