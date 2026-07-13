from datetime import datetime, timezone
from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_current_user,
    verify_jwt_in_request,
)
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.user import User
from app.schemas.auth import (
    RegisterSchema,
    LoginSchema,
    UpdateProfileSchema,
    ChangePasswordSchema,
    RequestEmailCodeSchema,
    OAuthAuthorizeSchema,
    OAuthCallbackSchema,
)
from app.schemas.ssh_key import CreateSshKeySchema, SshKeySchema
from app.services.auth_service import AuthService
from app.services.email_code_service import EmailCodeService
from app.services.user_service import UserService
from app.services.ssh_key_service import SshKeyService
from app.services.gitea_client import GiteaClient
from app.services.gitea_oauth_service import GiteaOAuthService

auth_bp = Blueprint("auth", __name__)


def _get_user_or_401():
    """Get current user or return 401 if not found (e.g. deleted after token issue)."""
    user = get_current_user()
    if user is None:
        return None, (jsonify(error="Unauthorized", message="User not found."), 401)
    return user, None


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    try:
        data = RegisterSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    try:
        user = AuthService.register_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            display_name=data.get("display_name"),
        )
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="Conflict", message="Username or email already taken."), 409
    except ValueError as e:
        return jsonify(error="Conflict", message=str(e)), 409

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify(
        user=user.to_dict(),
        access_token=access_token,
        refresh_token=refresh_token,
    ), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login and return tokens."""
    try:
        data = LoginSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    user = AuthService.authenticate(email=data["email"], password=data["password"])
    if user is None:
        return jsonify(error="Unauthorized", message="Invalid email or password."), 401

    # Update last login
    try:
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()
    except Exception:
        db.session.rollback()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify(
        user=user.to_dict(),
        access_token=access_token,
        refresh_token=refresh_token,
    ), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    user, error = _get_user_or_401()
    if error:
        return error
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Get current user info."""
    user, error = _get_user_or_401()
    if error:
        return error
    return jsonify(user=user.to_dict()), 200


@auth_bp.route("/me", methods=["PATCH"])
@jwt_required()
def update_me():
    """Update current user profile."""
    try:
        data = UpdateProfileSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    user, error = _get_user_or_401()
    if error:
        return error

    try:
        UserService.update_profile(user, data)
    except Exception:
        db.session.rollback()
        raise

    return jsonify(user=user.to_dict()), 200


@auth_bp.route("/email-code", methods=["POST"])
@jwt_required()
def request_email_code():
    """发送邮箱验证码（需登录）。用于修改密码、关闭/恢复 2FA。"""
    try:
        data = RequestEmailCodeSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    user, error = _get_user_or_401()
    if error:
        return error

    try:
        EmailCodeService.send_code(user.email, data["purpose"])
    except ValueError as e:
        return jsonify(error="Too Many Requests", message=str(e)), 429
    except Exception as e:
        return jsonify(error="Internal Server Error", message=str(e)), 500

    return jsonify(message="验证码已发送，请查收邮箱。"), 200


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """修改密码（需邮箱验证码）。"""
    try:
        data = ChangePasswordSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    user, error = _get_user_or_401()
    if error:
        return error

    try:
        AuthService.change_password(
            user=user,
            verification_code=data["verification_code"],
            new_password=data["new_password"],
        )
    except ValueError as e:
        return jsonify(error="Forbidden", message=str(e)), 403
    except Exception as e:
        return jsonify(error="Internal Server Error", message=str(e)), 500

    return jsonify(message="密码已修改，请使用新密码重新登录。"), 200


@auth_bp.route("/avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    """上传头像（multipart/form-data），返回 avatar_url。"""
    user, error = _get_user_or_401()
    if error:
        return error

    if "file" not in request.files:
        return jsonify(error="Bad Request", message="缺少 file 字段。"), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify(error="Bad Request", message="未选择文件。"), 400

    mime_type = file.content_type or file.mimetype or "application/octet-stream"

    try:
        UserService.save_avatar(user, file.stream, mime_type)
    except ValueError as e:
        return jsonify(error="Bad Request", message=str(e)), 400
    except Exception as e:
        return jsonify(error="Internal Server Error", message=str(e)), 500

    return jsonify(avatar_url=user.get_avatar_url(), user=user.to_dict()), 200


@auth_bp.route("/ssh-keys", methods=["GET"])
@jwt_required()
def list_ssh_keys():
    """获取当前用户的 SSH 公钥列表。"""
    user, error = _get_user_or_401()
    if error:
        return error
    keys = SshKeyService.list_keys(user)
    return jsonify(keys=SshKeySchema(many=True).dump(keys)), 200


@auth_bp.route("/ssh-keys", methods=["POST"])
@jwt_required()
def create_ssh_key():
    """添加 SSH 公钥并同步到 Gitea。"""
    try:
        data = CreateSshKeySchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    user, error = _get_user_or_401()
    if error:
        return error

    try:
        key = SshKeyService.add_key(user, data["title"], data["public_key"])
    except ValueError as e:
        return jsonify(error="Bad Request", message=str(e)), 400
    except Exception as e:
        return jsonify(error="Internal Server Error", message=str(e)), 500

    return jsonify(key=SshKeySchema().dump(key)), 201


@auth_bp.route("/ssh-keys/<key_id>", methods=["DELETE"])
@jwt_required()
def delete_ssh_key(key_id: str):
    """删除当前用户的指定 SSH 公钥。

    Query: ?force=true -- Gitea 不可用时强制删除本地记录。
    """
    user, error = _get_user_or_401()
    if error:
        return error

    force = request.args.get("force", "").lower() in ("true", "1", "yes")

    try:
        SshKeyService.delete_key(user, key_id, force=force)
    except ValueError as e:
        return jsonify(error="Not Found", message=str(e)), 404
    except RuntimeError as e:
        return jsonify(error="Service Unavailable", message=str(e)), 503
    except Exception as e:
        return jsonify(error="Internal Server Error", message=str(e)), 500

    return jsonify(message="公钥已删除。"), 200


@auth_bp.route("/ssh-keys/<key_id>/sync", methods=["POST"])
@jwt_required()
def retry_ssh_key_sync(key_id: str):
    """重试同步 SSH 公钥到 Gitea。"""
    user, error = _get_user_or_401()
    if error:
        return error

    try:
        from app.models.user_ssh_key import UserSshKey
        key = UserSshKey.query.filter_by(id=key_id, user_id=user.id).first()
        if key is None:
            return jsonify(error="Not Found", message="公钥不存在。"), 404
        key = SshKeyService.retry_sync(key, user)
    except Exception as e:
        return jsonify(error="Internal Server Error", message=str(e)), 500

    return jsonify(key=SshKeySchema().dump(key)), 200


@auth_bp.route("/oauth/gitea/authorize", methods=["GET"])
def oauth_authorize():
    """
    Query: ?intent=login|bind
    bind 需要 JWT 认证。
    Response 200: { "authorization_url": string }
    """
    try:
        data = OAuthAuthorizeSchema().load(request.args.to_dict())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    intent = data["intent"]
    user_id = None
    if intent == "bind":
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify(error="Unauthorized", message="Bind requires authentication."), 401
        user, error = _get_user_or_401()
        if error:
            return error
        user_id = user.id

    client_id = current_app.config.get("GITEA_OAUTH_CLIENT_ID", "")
    client_secret = current_app.config.get("GITEA_OAUTH_CLIENT_SECRET", "")
    gitea_url = current_app.config.get("GITEA_URL", "")
    if not client_id or not client_secret or not gitea_url:
        return jsonify(
            error="Service Unavailable",
            message="Gitea OAuth is not configured.",
        ), 503

    authorization_url = GiteaOAuthService.build_authorization_url(intent, user_id)
    return jsonify(authorization_url=authorization_url), 200


@auth_bp.route("/oauth/gitea/callback", methods=["GET"])
def oauth_callback():
    """
    Query: ?code=...&state=...
    login 成功: { user, access_token, refresh_token }
    bind 成功: { user }
    """
    try:
        data = OAuthCallbackSchema().load(request.args.to_dict())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    try:
        state_payload = GiteaOAuthService._decode_state(data["state"])
    except Exception:
        return jsonify(error="Bad Request", message="Invalid or expired state."), 400

    intent = state_payload.get("intent")
    if intent not in ("login", "bind"):
        return jsonify(error="Bad Request", message="Invalid state intent."), 400

    token_data = GiteaOAuthService.exchange_code(data["code"])
    if token_data is None:
        return jsonify(
            error="Service Unavailable",
            message="Gitea OAuth service is unavailable.",
        ), 503

    access_token = token_data.get("access_token")
    if not access_token:
        return jsonify(
            error="Service Unavailable",
            message="Gitea OAuth did not return an access token.",
        ), 503

    gitea_user = GiteaOAuthService.fetch_gitea_user(access_token)
    if gitea_user is None:
        return jsonify(
            error="Service Unavailable",
            message="Unable to fetch Gitea user profile.",
        ), 503

    if intent == "login":
        existing = GiteaOAuthService.find_user_by_gitea(gitea_user)
        if existing is None:
            return jsonify(
                error="Not Found",
                message="This Gitea account is not bound to any Codeersite user.",
            ), 404

        existing.last_login_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify(
            user=existing.to_dict(),
            access_token=create_access_token(identity=existing.id),
            refresh_token=create_refresh_token(identity=existing.id),
        ), 200

    # intent == "bind"
    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify(error="Unauthorized", message="Bind requires authentication."), 401

    user, error = _get_user_or_401()
    if error:
        return error

    state_user_id = state_payload.get("user_id")
    if state_user_id != user.id:
        return jsonify(error="Forbidden", message="State user mismatch."), 403

    existing = GiteaOAuthService.find_user_by_gitea(gitea_user)
    if existing is not None and existing.id != user.id:
        return jsonify(
            error="Conflict",
            message="This Gitea account is already bound to another user.",
        ), 409

    GiteaOAuthService.bind(user, gitea_user, token_data)
    return jsonify(user=user.to_dict()), 200


@auth_bp.route("/git-credentials", methods=["GET"])
@jwt_required()
def git_credentials():
    """
    Query: ?repo=<full_name>
    Response 200: { "clone_url_with_credentials": string }
    """
    repo = request.args.get("repo", "").strip()
    if not repo:
        return jsonify(error="Bad Request", message="Missing repo parameter."), 400

    user, error = _get_user_or_401()
    if error:
        return error

    clone_url = GiteaClient.get_authenticated_clone_url(user, repo)
    if clone_url is None:
        return jsonify(
            error="Service Unavailable",
            message="No valid Gitea token available.",
        ), 503

    return jsonify(clone_url_with_credentials=clone_url), 200
