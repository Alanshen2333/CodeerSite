"""Issue #18: Kanban reorder/move 边界校验。"""

import pytest


def _login(client, username, email):
    client.post("/api/auth/register", json={
        "username": username, "email": email, "password": "password123",
    })
    resp = client.post("/api/auth/login", json={
        "email": email, "password": "password123",
    })
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def _create_project(client, headers, name="Kanban Project"):
    resp = client.post(
        "/api/projects",
        json={"name": name, "visibility": "public"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["project"]


def _create_column(client, headers, slug, title):
    resp = client.post(
        f"/api/projects/{slug}/kanban/columns",
        json={"title": title},
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["column"]


def _create_card(client, headers, slug, column_id, title):
    resp = client.post(
        f"/api/projects/{slug}/kanban/columns/{column_id}/cards",
        json={"title": title},
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["card"]


@pytest.mark.usefixtures("auth_headers")
class TestReorderColumns:
    def test_valid_reorder(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]
        c1 = _create_column(client, auth_headers, slug, "Todo")
        c2 = _create_column(client, auth_headers, slug, "Doing")
        c3 = _create_column(client, auth_headers, slug, "Done")

        resp = client.post(
            f"/api/projects/{slug}/kanban/columns/reorder",
            json={"column_ids": [c3["id"], c1["id"], c2["id"]]},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # Verify order
        resp = client.get(f"/api/projects/{slug}/kanban/columns")
        cols = resp.get_json()["columns"]
        assert cols[0]["id"] == c3["id"]
        assert cols[1]["id"] == c1["id"]
        assert cols[2]["id"] == c2["id"]

    def test_missing_column_id(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]
        c1 = _create_column(client, auth_headers, slug, "Todo")
        _create_column(client, auth_headers, slug, "Doing")

        # Only provide one of two columns
        resp = client.post(
            f"/api/projects/{slug}/kanban/columns/reorder",
            json={"column_ids": [c1["id"]]},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_duplicate_column_id(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]
        c1 = _create_column(client, auth_headers, slug, "Todo")
        c2 = _create_column(client, auth_headers, slug, "Doing")

        resp = client.post(
            f"/api/projects/{slug}/kanban/columns/reorder",
            json={"column_ids": [c1["id"], c1["id"], c2["id"]]},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_cross_project_column_id(self, client, auth_headers):
        p1 = _create_project(client, auth_headers, name="Project A")
        p2 = _create_project(client, auth_headers, name="Project B")
        c1 = _create_column(client, auth_headers, p1["slug"], "A-Todo")
        foreign = _create_column(client, auth_headers, p2["slug"], "B-Todo")

        resp = client.post(
            f"/api/projects/{p1['slug']}/kanban/columns/reorder",
            json={"column_ids": [foreign["id"], c1["id"]]},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_empty_column_ids(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]
        _create_column(client, auth_headers, slug, "Todo")

        resp = client.post(
            f"/api/projects/{slug}/kanban/columns/reorder",
            json={"column_ids": []},
            headers=auth_headers,
        )
        assert resp.status_code == 422


@pytest.mark.usefixtures("auth_headers")
class TestMoveCardValidation:
    def test_move_to_negative_position(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]
        col = _create_column(client, auth_headers, slug, "Todo")
        _create_card(client, auth_headers, slug, col["id"], "Card 1")

        resp = client.post(
            f"/api/projects/{slug}/kanban/cards/999/move",
            json={"column_id": col["id"], "position": -5},
            headers=auth_headers,
        )
        # Card 999 doesn't exist -> 404 (not 400, since card lookup fails first)
        assert resp.status_code == 404

    def test_move_within_same_column_negative(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]
        col = _create_column(client, auth_headers, slug, "Todo")
        card = _create_card(client, auth_headers, slug, col["id"], "Card 1")

        resp = client.post(
            f"/api/projects/{slug}/kanban/cards/{card['id']}/move",
            json={"column_id": col["id"], "position": -10},
            headers=auth_headers,
        )
        # Negative position gets clamped to 0, should succeed
        assert resp.status_code == 200
        assert resp.get_json()["card"]["position"] == 0

    def test_move_beyond_end_clamped(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]
        col = _create_column(client, auth_headers, slug, "Todo")
        card1 = _create_card(client, auth_headers, slug, col["id"], "Card 1")
        _create_card(client, auth_headers, slug, col["id"], "Card 2")

        # Move card1 to position 999 -> should clamp to 1 (last position)
        resp = client.post(
            f"/api/projects/{slug}/kanban/cards/{card1['id']}/move",
            json={"column_id": col["id"], "position": 999},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["card"]["position"] == 1

    def test_cross_column_move_clamped(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]
        col1 = _create_column(client, auth_headers, slug, "Todo")
        col2 = _create_column(client, auth_headers, slug, "Done")
        card = _create_card(client, auth_headers, slug, col1["id"], "Card 1")

        # Move to col2 at position 999 -> col2 has 0 cards, clamp to 0
        resp = client.post(
            f"/api/projects/{slug}/kanban/cards/{card['id']}/move",
            json={"column_id": col2["id"], "position": 999},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()["card"]
        assert data["column_id"] == col2["id"]
        assert data["position"] == 0

    def test_positions_contiguous_after_move(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]
        col = _create_column(client, auth_headers, slug, "Todo")
        card1 = _create_card(client, auth_headers, slug, col["id"], "Card 1")
        card2 = _create_card(client, auth_headers, slug, col["id"], "Card 2")
        card3 = _create_card(client, auth_headers, slug, col["id"], "Card 3")

        # Move card3 to front (position 0)
        resp = client.post(
            f"/api/projects/{slug}/kanban/cards/{card3['id']}/move",
            json={"column_id": col["id"], "position": 0},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # Verify card3 is now first, others shifted after it
        resp = client.get(f"/api/projects/{slug}/kanban/columns")
        cards = resp.get_json()["columns"][0]["cards"]
        # card3 should be at position 0, the rest after it in order
        assert cards[0]["id"] == card3["id"]
        assert cards[1]["id"] == card1["id"]
        assert cards[2]["id"] == card2["id"]
        # No holes: positions should be contiguous starting from 0
        positions = sorted(c["position"] for c in cards)
        assert positions == list(range(len(positions)))
