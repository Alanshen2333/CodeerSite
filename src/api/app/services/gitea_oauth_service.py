"""Gitea OAuth2 绑定/登录服务。"""
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from flask import current_app
from flask_jwt_extended import create_access_token, decode_token

from app.extensions import db
from app.models.user import User
from app.services.gitea_client import GiteaClient


class GiteaOAuthService:
    STATE_PURPOSE = "oauth_state"
    SCOPE = "read:user read:repository write:repository"

    @staticmethod
    def build_authorization_url(intent: str, user_id: str | None = None) -> str:
        """返回带签名 state 的 Gitea /login/oauth/authorize URL。"""
        client_id = current_app.config.get("GITEA_OAUTH_CLIENT_ID", "")
        redirect_uri = current_app.config.get(
            "GITEA_OAUTH_REDIRECT_URI", "http://localhost:3000/oauth/gitea"
        )
        state = GiteaOAuthService._generate_state(intent, user_id)
        base_url = current_app.config.get("GITEA_URL", "").rstrip("/")
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": GiteaOAuthService.SCOPE,
        }
        return f"{base_url}/login/oauth/authorize?{urlencode(params)}"

    @staticmethod
    def _generate_state(intent: str, user_id: str | None = None) -> str:
        """用 flask_jwt_extended 创建 5 分钟有效 state JWT。"""
        return create_access_token(
            identity="",
            expires_delta=timedelta(minutes=5),
            additional_claims={
                "purpose": GiteaOAuthService.STATE_PURPOSE,
                "intent": intent,
                "user_id": user_id,
            },
        )

    @staticmethod
    def _decode_state(state: str) -> dict:
        """校验 state JWT；失败抛出 ValueError。"""
        payload = decode_token(state)
        if payload.get("purpose") != GiteaOAuthService.STATE_PURPOSE:
            raise ValueError("Invalid state purpose")
        return {
            "intent": payload.get("intent"),
            "user_id": payload.get("user_id"),
        }

    @staticmethod
    def exchange_code(code: str) -> dict | None:
        """调 GiteaClient.exchange_oauth_code。"""
        redirect_uri = current_app.config.get(
            "GITEA_OAUTH_REDIRECT_URI", "http://localhost:3000/oauth/gitea"
        )
        return GiteaClient.exchange_oauth_code(code, redirect_uri)

    @staticmethod
    def fetch_gitea_user(access_token: str) -> dict | None:
        """调 GiteaClient.get_oauth_user。"""
        return GiteaClient.get_oauth_user(access_token)

    @staticmethod
    def bind(user: User, gitea_user: dict, token_data: dict) -> None:
        """保存 gitea_user_id、token、refresh token、expires_at。"""
        gitea_user_id = str(gitea_user.get("id"))
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")
        expires_at = None
        if expires_in:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        user.gitea_user_id = gitea_user_id
        user.set_gitea_tokens(access_token, refresh_token, expires_at)
        db.session.commit()

    @staticmethod
    def find_user_by_gitea(gitea_user: dict) -> User | None:
        """按 gitea_user_id 查找 Codeersite 用户。"""
        gitea_user_id = str(gitea_user.get("id"))
        return User.query.filter_by(gitea_user_id=gitea_user_id).first()
