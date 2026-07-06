"""SSH 公钥管理服务。

负责：
1. 解析并校验 OpenSSH 格式公钥。
2. 计算 SHA-256 fingerprint。
3. 与 Gitea 同步（添加/删除）。
4. 本地持久化与去重。
"""
import base64
import hashlib
import re

from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import UnsupportedAlgorithm
from flask import current_app

from app.extensions import db
from app.models.user_ssh_key import UserSshKey
from app.services.gitea_client import GiteaClient

# OpenSSH 公钥基础格式：type base64-body [comment]
_SSH_KEY_RE = re.compile(r"^(?P<type>ssh-[a-z0-9-]+|ecdsa-sha2-[a-z0-9-]+)\s+(?P<body>[A-Za-z0-9+/=]+)(?:\s+.*)?$")


class SshKeyService:
    @staticmethod
    def _parse_raw_key(key_text: str) -> tuple[str, str]:
        """从 OpenSSH 单行公钥中提取 key_type 与 base64 body。

        返回 (key_type, key_data)；格式不合法时抛出 ValueError。
        """
        text = key_text.strip()
        if not text:
            raise ValueError("公钥内容不能为空。")

        match = _SSH_KEY_RE.match(text)
        if not match:
            raise ValueError("公钥格式不正确，应为 OpenSSH 单行格式（如 ssh-ed25519 AAAAC3...）。")

        key_type = match.group("type")
        key_data = match.group("body")

        # cryptography 需要完整的 OpenSSH 公钥数据（含类型前缀）
        try:
            pub_key = serialization.load_ssh_public_key(key_text.encode("ascii"))
        except UnsupportedAlgorithm as exc:
            raise ValueError(f"不支持的公钥类型：{key_type}。") from exc
        except Exception as exc:
            raise ValueError("无法解析该公钥，请检查内容是否完整。") from exc

        # 序列化回 OpenSSH 格式以确认类型（避免声明 ssh-rsa 实际为 ed25519）
        serialized = pub_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )
        actual_type = serialized.split(b" ", 1)[0].decode("ascii")
        if actual_type != key_type:
            raise ValueError(f"公钥类型不匹配：声明为 {key_type}，实际为 {actual_type}。")

        return key_type, key_data

    @staticmethod
    def _fingerprint(key_data: str) -> str:
        """计算 SHA-256 fingerprint（OpenSSH 风格，无尾部等号）。"""
        raw = base64.b64decode(key_data)
        digest = hashlib.sha256(raw).digest()
        fp = base64.b64encode(digest).decode("ascii").rstrip("=")
        return f"SHA256:{fp}"

    @staticmethod
    def validate_public_key(key_text: str) -> tuple[str, str, str]:
        """校验公钥并返回 (key_type, key_data, fingerprint)。"""
        key_type, key_data = SshKeyService._parse_raw_key(key_text)
        fingerprint = SshKeyService._fingerprint(key_data)
        return key_type, key_data, fingerprint

    @staticmethod
    def list_keys(user) -> list[UserSshKey]:
        """返回用户所有 SSH 公钥（按创建时间倒序）。"""
        return (
            UserSshKey.query.filter_by(user_id=user.id)
            .order_by(UserSshKey.created_at.desc())
            .all()
        )

    @staticmethod
    def add_key(user, title: str, key_text: str) -> UserSshKey:
        """添加 SSH 公钥并同步到 Gitea。

        流程：
        1. 校验公钥格式。
        2. 检查 fingerprint 全局唯一。
        3. 调用 Gitea admin API 添加公钥；Gitea 不可用时抛出 503。
        4. 保存本地记录。
        """
        title = title.strip()
        if not title:
            raise ValueError("请输入公钥标题。")
        if len(title) > 100:
            raise ValueError("标题不能超过 100 个字符。")

        key_type, key_data, fingerprint = SshKeyService.validate_public_key(key_text)

        existing = UserSshKey.query.filter_by(fingerprint=fingerprint).first()
        if existing:
            raise ValueError("该公钥已存在，请勿重复添加。")

        # 同步到 Gitea
        gitea_key_id = None
        if GiteaClient._is_available():
            gitea_resp = GiteaClient._admin_request(
                "POST",
                f"/api/v1/admin/users/{user.username}/keys",
                json={"title": title, "key": f"{key_type} {key_data}"},
            )
            if gitea_resp is None:
                raise RuntimeError("Gitea 服务暂不可用，请稍后重试。")
            if gitea_resp.status_code not in (200, 201):
                current_app.logger.warning(
                    "Gitea 添加 SSH key 失败 %s: %s", gitea_resp.status_code, gitea_resp.text[:200]
                )
                raise RuntimeError("同步公钥到 Gitea 失败，请检查公钥格式或稍后重试。")
            gitea_data = gitea_resp.json()
            gitea_key_id = str(gitea_data.get("id"))
        else:
            raise RuntimeError("Gitea 服务未配置或不可达，暂无法添加 SSH 公钥。")

        key = UserSshKey(
            user_id=user.id,
            title=title,
            key_type=key_type,
            key_data=key_data,
            fingerprint=fingerprint,
            gitea_key_id=gitea_key_id,
        )
        db.session.add(key)
        db.session.commit()
        return key

    @staticmethod
    def delete_key(user, key_id: str) -> None:
        """删除用户 SSH 公钥，并同步从 Gitea 移除。"""
        key = UserSshKey.query.filter_by(id=key_id, user_id=user.id).first()
        if key is None:
            raise ValueError("公钥不存在。")

        if key.gitea_key_id and GiteaClient._is_available():
            resp = GiteaClient._admin_request(
                "DELETE",
                f"/api/v1/admin/users/{user.username}/keys/{key.gitea_key_id}",
            )
            # 404 表示 Gitea 端已不存在，视为成功
            if resp is None:
                raise RuntimeError("Gitea 服务暂不可用，请稍后重试。")
            if resp.status_code not in (204, 404):
                current_app.logger.warning(
                    "Gitea 删除 SSH key 失败 %s: %s", resp.status_code, resp.text[:200]
                )
                raise RuntimeError("从 Gitea 删除公钥失败，请稍后重试。")

        db.session.delete(key)
        db.session.commit()
