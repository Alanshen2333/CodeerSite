"""Issue #19: SSH Key Gitea 同步补偿机制（最终一致）。"""

from unittest.mock import patch, MagicMock

import pytest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from app.extensions import db
from app.models.user_ssh_key import UserSshKey


def _gen_key() -> str:
    """生成一个唯一的 ed25519 公钥用于测试。"""
    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes(
        serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH
    )
    return pub.decode()


def _mock_response(status=200, data=None):
    resp = MagicMock()
    resp.status_code = status
    resp.text = "error detail"
    resp.json.return_value = data or {}
    return resp


@pytest.mark.usefixtures("auth_headers")
class TestSshKeySync:
    @patch("app.services.ssh_key_service.GiteaClient")
    def test_add_key_gitea_success(self, mock_gitea, client, auth_headers):
        """Gitea 可用且同步成功 -> sync_status=synced。返回 201。"""
        mock_gitea._is_available.return_value = True
        mock_gitea._admin_request.return_value = _mock_response(201, {"id": 42})

        resp = client.post("/api/auth/ssh-keys", json={
            "title": "My Key",
            "public_key": _gen_key(),
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.get_json()
        data = resp.get_json()["key"]
        assert data["sync_status"] == "synced"
        assert data["gitea_key_id"] == "42"

    @patch("app.services.ssh_key_service.GiteaClient")
    def test_add_key_gitea_unavailable(self, mock_gitea, client, auth_headers):
        """Gitea 不可用 -> 本地仍保存，sync_status=pending，返回 201。"""
        mock_gitea._is_available.return_value = False

        resp = client.post("/api/auth/ssh-keys", json={
            "title": "My Key",
            "public_key": _gen_key(),
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.get_json()
        data = resp.get_json()["key"]
        assert data["sync_status"] == "pending"
        assert data["gitea_key_id"] is None

    @patch("app.services.ssh_key_service.GiteaClient")
    def test_add_key_gitea_failure(self, mock_gitea, client, auth_headers):
        """Gitea 返回错误 -> sync_status=failed，本地仍保存，返回 201。"""
        mock_gitea._is_available.return_value = True
        mock_gitea._admin_request.return_value = _mock_response(500)

        resp = client.post("/api/auth/ssh-keys", json={
            "title": "My Key",
            "public_key": _gen_key(),
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.get_json()
        data = resp.get_json()["key"]
        assert data["sync_status"] == "failed"
        assert data["sync_error"] is not None

    @patch("app.services.ssh_key_service.GiteaClient")
    def test_retry_sync_success(self, mock_gitea, client, app, auth_headers):
        """pending 状态的 key 重试同步成功 -> synced。"""
        mock_gitea._is_available.return_value = False
        resp = client.post("/api/auth/ssh-keys", json={
            "title": "My Key",
            "public_key": _gen_key(),
        }, headers=auth_headers)
        assert resp.status_code == 201
        key_id = resp.get_json()["key"]["id"]

        # Gitea becomes available, retry
        mock_gitea._is_available.return_value = True
        mock_gitea._admin_request.return_value = _mock_response(201, {"id": 99})

        resp = client.post(f"/api/auth/ssh-keys/{key_id}/sync", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()["key"]
        assert data["sync_status"] == "synced"
        assert data["gitea_key_id"] == "99"

    @patch("app.services.ssh_key_service.GiteaClient")
    def test_retry_sync_still_fails(self, mock_gitea, client, auth_headers):
        """重试同步仍然失败 -> sync_status=failed。"""
        mock_gitea._is_available.return_value = False
        resp = client.post("/api/auth/ssh-keys", json={
            "title": "My Key",
            "public_key": _gen_key(),
        }, headers=auth_headers)
        key_id = resp.get_json()["key"]["id"]

        mock_gitea._is_available.return_value = True
        mock_gitea._admin_request.return_value = _mock_response(500)

        resp = client.post(f"/api/auth/ssh-keys/{key_id}/sync", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["key"]["sync_status"] == "failed"

    @patch("app.services.ssh_key_service.GiteaClient")
    def test_delete_gitea_success(self, mock_gitea, client, auth_headers):
        """Gitea 可用且删除成功 -> 本地删除。"""
        mock_gitea._is_available.return_value = True
        mock_gitea._admin_request.return_value = _mock_response(201, {"id": 42})
        resp = client.post("/api/auth/ssh-keys", json={
            "title": "My Key",
            "public_key": _gen_key(),
        }, headers=auth_headers)
        key_id = resp.get_json()["key"]["id"]

        mock_gitea._admin_request.return_value = _mock_response(204)
        resp = client.delete(f"/api/auth/ssh-keys/{key_id}", headers=auth_headers)
        assert resp.status_code == 200

    @patch("app.services.ssh_key_service.GiteaClient")
    def test_delete_gitea_unavailable_no_force(self, mock_gitea, client, auth_headers):
        """Gitea 不可用且未 force -> 503。"""
        mock_gitea._is_available.return_value = True
        mock_gitea._admin_request.return_value = _mock_response(201, {"id": 42})
        resp = client.post("/api/auth/ssh-keys", json={
            "title": "My Key",
            "public_key": _gen_key(),
        }, headers=auth_headers)
        key_id = resp.get_json()["key"]["id"]

        mock_gitea._is_available.return_value = False
        resp = client.delete(f"/api/auth/ssh-keys/{key_id}", headers=auth_headers)
        assert resp.status_code == 503

    @patch("app.services.ssh_key_service.GiteaClient")
    def test_delete_gitea_unavailable_force(self, mock_gitea, client, auth_headers):
        """Gitea 不可用但 force=true -> 强制删除本地记录。"""
        mock_gitea._is_available.return_value = True
        mock_gitea._admin_request.return_value = _mock_response(201, {"id": 42})
        resp = client.post("/api/auth/ssh-keys", json={
            "title": "My Key",
            "public_key": _gen_key(),
        }, headers=auth_headers)
        key_id = resp.get_json()["key"]["id"]

        mock_gitea._is_available.return_value = False
        resp = client.delete(f"/api/auth/ssh-keys/{key_id}?force=true", headers=auth_headers)
        assert resp.status_code == 200

    @patch("app.services.ssh_key_service.GiteaClient")
    def test_delete_unsynced_key_without_gitea(self, mock_gitea, client, auth_headers):
        """删除未同步的 key（无 gitea_key_id）-> 直接删除，无需 force。"""
        mock_gitea._is_available.return_value = False
        resp = client.post("/api/auth/ssh-keys", json={
            "title": "My Key",
            "public_key": _gen_key(),
        }, headers=auth_headers)
        assert resp.status_code == 201
        key_id = resp.get_json()["key"]["id"]

        resp = client.delete(f"/api/auth/ssh-keys/{key_id}", headers=auth_headers)
        assert resp.status_code == 200

    @patch("app.services.ssh_key_service.GiteaClient")
    def test_delete_gitea_delete_fails_no_force(self, mock_gitea, client, auth_headers):
        """Gitea 可用但删除返回错误且未 force -> 503。"""
        mock_gitea._is_available.return_value = True
        mock_gitea._admin_request.return_value = _mock_response(201, {"id": 42})
        resp = client.post("/api/auth/ssh-keys", json={
            "title": "My Key",
            "public_key": _gen_key(),
        }, headers=auth_headers)
        key_id = resp.get_json()["key"]["id"]

        mock_gitea._admin_request.return_value = _mock_response(500)
        resp = client.delete(f"/api/auth/ssh-keys/{key_id}", headers=auth_headers)
        assert resp.status_code == 503

    @patch("app.services.ssh_key_service.GiteaClient")
    def test_delete_gitea_delete_fails_force(self, mock_gitea, client, auth_headers):
        """Gitea 可用但删除返回错误，force=true -> 强制删除。"""
        mock_gitea._is_available.return_value = True
        mock_gitea._admin_request.return_value = _mock_response(201, {"id": 42})
        resp = client.post("/api/auth/ssh-keys", json={
            "title": "My Key",
            "public_key": _gen_key(),
        }, headers=auth_headers)
        key_id = resp.get_json()["key"]["id"]

        mock_gitea._admin_request.return_value = _mock_response(500)
        resp = client.delete(f"/api/auth/ssh-keys/{key_id}?force=true", headers=auth_headers)
        assert resp.status_code == 200
