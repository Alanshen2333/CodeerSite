"""Token 加密工具 —— 用于加密缓存的 Gitea personal access token。"""
from flask import current_app
from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Fernet | None:
    """从应用配置构造 Fernet 实例；未配置或非法时返回 None。"""
    key = current_app.config.get("GITEA_TOKEN_ENCRYPTION_KEY")
    if not key:
        return None
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        current_app.logger.warning("GITEA_TOKEN_ENCRYPTION_KEY 无效，无法初始化 Fernet")
        return None


def encrypt_token(plain: str) -> str | None:
    """加密明文字符串；失败返回 None。"""
    if not plain:
        return None
    fernet = _get_fernet()
    if fernet is None:
        return None
    try:
        return fernet.encrypt(plain.encode("utf-8")).decode("utf-8")
    except Exception as exc:
        current_app.logger.warning("加密 token 失败: %s", exc)
        return None


def decrypt_token(cipher: str | None) -> str | None:
    """解密密文字符串；失败返回 None。"""
    if not cipher:
        return None
    fernet = _get_fernet()
    if fernet is None:
        return None
    try:
        return fernet.decrypt(cipher.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        current_app.logger.warning("解密 token 失败: invalid token")
        return None
    except Exception as exc:
        current_app.logger.warning("解密 token 失败: %s", exc)
        return None
