"""Gitea API 客户端。

设计原则：
1. 所有 admin 操作使用配置里的 GITEA_ADMIN_TOKEN。
2. 用户代理请求使用当前用户的 Gitea token（解密后）。
3. Gitea 不可用时返回 None 而不是抛异常，调用方负责降级。
4. 用户 token 失效（401）时尝试用 admin API 重新签发一次。
"""
from __future__ import annotations

import secrets
import string
from typing import TYPE_CHECKING

import httpx
from flask import current_app

from app.utils.crypto import decrypt_token, encrypt_token

if TYPE_CHECKING:
    from app.models.user import User

# 模块级 HTTP 客户端单例
_client: httpx.Client | None = None


def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(
            timeout=httpx.Timeout(3.0, connect=1.5),
            follow_redirects=True,
        )
    return _client


def _base_url() -> str:
    return current_app.config.get("GITEA_URL", "").rstrip("/")


def _admin_token() -> str:
    return current_app.config.get("GITEA_ADMIN_TOKEN", "")


def _org_name() -> str:
    return current_app.config.get("GITEA_ORG", "codeersite")


def _admin_auth_headers() -> dict:
    return {"Authorization": f"token {_admin_token()}"}


def _admin_basic_auth() -> httpx.BasicAuth | None:
    """部分 admin 端点（如创建 token）仅接受 basic auth。"""
    user = current_app.config.get("GITEA_ADMIN_USER")
    passwd = current_app.config.get("GITEA_ADMIN_PASS")
    if user and passwd:
        return httpx.BasicAuth(user, passwd)
    return None


class GiteaClient:
    """Gitea admin/utility 客户端。"""

    @staticmethod
    def _is_available() -> bool:
        """检查 Gitea URL 与 admin token 已配置且 /api/v1/version 可达。"""
        url = _base_url()
        token = _admin_token()
        if not url or not token:
            return False
        try:
            resp = _get_client().get(
                f"{url}/api/v1/version",
                headers={"Authorization": f"token {token}"},
                timeout=2.0,
            )
            return resp.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _request(method: str, path: str, *, headers: dict | None = None, **kwargs) -> httpx.Response | None:
        """底层请求封装；网络/超时错误返回 None。"""
        url = _base_url()
        if not url:
            return None
        try:
            return _get_client().request(method, f"{url}{path}", headers=headers, **kwargs)
        except Exception as exc:
            current_app.logger.warning("Gitea 请求失败 %s %s: %s", method, path, exc)
            return None

    @staticmethod
    def _admin_request(method: str, path: str, **kwargs) -> httpx.Response | None:
        headers = kwargs.pop("headers", {})
        headers.update(_admin_auth_headers())
        return GiteaClient._request(method, path, headers=headers, **kwargs)

    @staticmethod
    def admin_create_user(username: str, email: str, password: str | None = None) -> dict | None:
        """同步创建 Gitea 用户；失败返回 None。"""
        if not password:
            password = _generate_password()
        payload = {
            "login_name": username,
            "username": username,
            "email": email,
            "password": password,
            "must_change_password": False,
            "send_notify": False,
        }
        resp = GiteaClient._admin_request("POST", "/api/v1/admin/users", json=payload)
        if resp is None:
            return None
        if resp.status_code == 201:
            return resp.json()
        if resp.status_code == 422 and "already exists" in resp.text:
            # 幂等：用户已存在时返回现有用户
            get_resp = GiteaClient._admin_request("GET", f"/api/v1/users/{username}")
            if get_resp and get_resp.status_code == 200:
                return get_resp.json()
        current_app.logger.warning(
            "Gitea 创建用户失败 %s: %s", resp.status_code, resp.text[:200]
        )
        return None

    @staticmethod
    def admin_create_org(name: str) -> dict | None:
        """幂等创建 org；已存在时返回现有 org。"""
        resp = GiteaClient._admin_request("POST", "/api/v1/orgs", json={"username": name})
        if resp is None:
            return None
        if resp.status_code in (201, 200):
            return resp.json()
        if resp.status_code == 422 and "already exists" in resp.text:
            get_resp = GiteaClient._admin_request("GET", f"/api/v1/orgs/{name}")
            if get_resp and get_resp.status_code == 200:
                return get_resp.json()
        current_app.logger.warning(
            "Gitea 创建 org 失败 %s: %s", resp.status_code, resp.text[:200]
        )
        return None

    @staticmethod
    def admin_create_user_token(username: str, token_name: str | None = None) -> str | None:
        """为指定用户创建 personal access token；返回 sha。

        注意：Gitea 的 /users/{username}/tokens 端点不接受 token auth，需用 basic auth；
        token name 在同一用户下必须唯一，因此默认使用带时间戳的名称。
        """
        from datetime import datetime, timezone

        auth = _admin_basic_auth()
        if auth is None:
            current_app.logger.warning("未配置 GITEA_ADMIN_USER/PASS，无法创建用户 token")
            return None
        name = token_name or f"codeersite-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        resp = GiteaClient._request(
            "POST",
            f"/api/v1/users/{username}/tokens",
            auth=auth,
            json={"name": name, "scopes": ["all"]},
        )
        if resp is None:
            return None
        if resp.status_code == 201:
            data = resp.json()
            return data.get("sha1")
        current_app.logger.warning(
            "Gitea 创建用户 token 失败 %s: %s", resp.status_code, resp.text[:200]
        )
        return None

    @staticmethod
    def admin_create_repo(org: str, name: str, description: str | None = None, private: bool = False) -> dict | None:
        """在指定 org 下创建仓库。"""
        payload = {
            "name": name,
            "description": description or "",
            "private": private,
            "default_branch": "main",
        }
        resp = GiteaClient._admin_request("POST", f"/api/v1/orgs/{org}/repos", json=payload)
        if resp is None:
            return None
        if resp.status_code == 201:
            return resp.json()
        current_app.logger.warning(
            "Gitea 创建仓库失败 %s: %s", resp.status_code, resp.text[:200]
        )
        return None

    @staticmethod
    def admin_get_repo(org: str, name: str) -> dict | None:
        """获取仓库元信息。"""
        resp = GiteaClient._admin_request("GET", f"/api/v1/repos/{org}/{name}")
        if resp is None:
            return None
        if resp.status_code == 200:
            return resp.json()
        return None

    @staticmethod
    def admin_delete_repo(org: str, name: str) -> bool:
        """删除仓库。"""
        resp = GiteaClient._admin_request("DELETE", f"/api/v1/repos/{org}/{name}")
        if resp is None:
            return False
        return resp.status_code in (204, 404)

    @staticmethod
    def admin_add_user_ssh_key(username: str, title: str, key_text: str) -> dict | None:
        """为指定用户添加 SSH 公钥；成功返回 Gitea key 对象，失败返回 None。"""
        resp = GiteaClient._admin_request(
            "POST",
            f"/api/v1/admin/users/{username}/keys",
            json={"title": title, "key": key_text},
        )
        if resp is None:
            return None
        if resp.status_code in (200, 201):
            return resp.json()
        current_app.logger.warning(
            "Gitea 添加用户 SSH key 失败 %s: %s", resp.status_code, resp.text[:200]
        )
        return None

    @staticmethod
    def admin_delete_user_ssh_key(username: str, gitea_key_id: str) -> bool:
        """删除指定用户的 SSH 公钥；404 视为成功。"""
        resp = GiteaClient._admin_request(
            "DELETE", f"/api/v1/admin/users/{username}/keys/{gitea_key_id}"
        )
        if resp is None:
            return False
        return resp.status_code in (204, 404)

    @staticmethod
    def for_user(user: User) -> UserGiteaClient | None:
        """构造当前用户的 Gitea 代理客户端。"""
        if not user.gitea_token_encrypted:
            return None
        token = decrypt_token(user.gitea_token_encrypted)
        if not token:
            # 尝试用 admin token 重新签发一次
            token = GiteaClient._reissue_user_token(user)
            if not token:
                return None
        return UserGiteaClient(user, token)

    @staticmethod
    def _reissue_user_token(user: User) -> str | None:
        """用 admin API 为用户重新签发 token 并加密保存。"""
        from app.extensions import db

        if not user.gitea_user_id or not user.username:
            return None
        new_token = GiteaClient.admin_create_user_token(user.username)
        if not new_token:
            return None
        encrypted = encrypt_token(new_token)
        if encrypted:
            user.gitea_token_encrypted = encrypted
            db.session.commit()
        return new_token


class UserGiteaClient:
    """以某个用户的 token 调用 Gitea API；支持 401 后重试一次。"""

    def __init__(self, user: User, token: str):
        self.user = user
        self.token = token

    def _headers(self) -> dict:
        return {"Authorization": f"token {self.token}"}

    def request(self, method: str, path: str, **kwargs) -> httpx.Response | None:
        """发起请求；401 时尝试重签发 token 并重试一次。"""
        resp = GiteaClient._request(method, path, headers=self._headers(), **kwargs)
        if resp is not None and resp.status_code == 401:
            new_token = GiteaClient._reissue_user_token(self.user)
            if new_token and new_token != self.token:
                self.token = new_token
                resp = GiteaClient._request(method, path, headers=self._headers(), **kwargs)
        return resp

    def get(self, path: str, **kwargs) -> httpx.Response | None:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> httpx.Response | None:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs) -> httpx.Response | None:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> httpx.Response | None:
        return self.request("DELETE", path, **kwargs)


class ReadOnlyGiteaClient:
    """使用固定 token 进行只读请求；用于公开项目匿名访问。"""

    def __init__(self, token: str):
        self.token = token

    def _headers(self) -> dict:
        return {"Authorization": f"token {self.token}"}

    def request(self, method: str, path: str, **kwargs) -> httpx.Response | None:
        return GiteaClient._request(method, path, headers=self._headers(), **kwargs)

    def get(self, path: str, **kwargs) -> httpx.Response | None:
        return self.request("GET", path, **kwargs)


def _generate_password(length: int = 32) -> str:
    """生成符合 Gitea 密码策略的随机强密码。"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in pwd)
            and any(c.isupper() for c in pwd)
            and any(c.isdigit() for c in pwd)
            and any(c in "!@#$%^&*" for c in pwd)
        ):
            return pwd
