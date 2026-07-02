"""Test Q&A endpoints: questions, answers, votes."""


class TestQuestions:
    def test_list_empty(self, client):
        resp = client.get("/api/questions")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["questions"] == []
        assert data["total"] == 0

    def test_create_question(self, client, auth_headers):
        resp = client.post("/api/questions", json={
            "title": "How to test?",
            "body": "This is a test question.",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["question"]["title"] == "How to test?"
        assert data["question"]["answer_count"] == 0

    def test_create_question_no_auth(self, client):
        resp = client.post("/api/questions", json={
            "title": "No auth",
            "body": "Should fail.",
        })
        assert resp.status_code == 401

    def test_get_single_question(self, client, auth_headers):
        create_resp = client.post("/api/questions", json={
            "title": "Single question",
            "body": "Content body here.",
        }, headers=auth_headers)
        q_id = create_resp.get_json()["question"]["id"]

        resp = client.get(f"/api/questions/{q_id}")
        assert resp.status_code == 200
        assert resp.get_json()["question"]["view_count"] == 1

    def test_delete_question(self, client, auth_headers):
        create_resp = client.post("/api/questions", json={
            "title": "Delete me please",
            "body": "Content body here.",
        }, headers=auth_headers)
        q_id = create_resp.get_json()["question"]["id"]

        resp = client.delete(f"/api/questions/{q_id}", headers=auth_headers)
        assert resp.status_code == 200

        resp = client.get(f"/api/questions/{q_id}")
        assert resp.status_code == 404

    def test_list_with_sorting(self, client, auth_headers):
        client.post("/api/questions", json={
            "title": "Question one", "body": "Body content one.",
        }, headers=auth_headers)
        client.post("/api/questions", json={
            "title": "Question two", "body": "Body content two.",
        }, headers=auth_headers)

        resp = client.get("/api/questions?sort=newest&per_page=2")
        data = resp.get_json()
        assert data["total"] == 2
        assert len(data["questions"]) == 2
