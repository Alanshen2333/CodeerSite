from urllib.parse import urlparse

import pytest
from sqlalchemy import create_engine, text

from app import create_app
from app.extensions import db
from app.services.email_code_service import EmailCodeService


def _ensure_test_database(uri: str) -> None:
    """如果测试数据库不存在，则自动创建（仅 PostgreSQL）。"""
    if not uri.startswith("postgresql"):
        return
    parsed = urlparse(uri)
    db_name = parsed.path.lstrip("/")
    if not db_name:
        return
    base_uri = (
        f"{parsed.scheme}://{parsed.username}:{parsed.password}"
        f"@{parsed.hostname}:{parsed.port or 5432}/postgres"
    )
    engine = create_engine(base_uri, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname=:name"),
                {"name": db_name},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        engine.dispose()


@pytest.fixture
def app():
    """每个测试使用独立的干净 schema。"""
    app = create_app("test")
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    _ensure_test_database(uri)

    with app.app_context():
        db.drop_all()
        # 创建 pg_trgm 扩展（用于 search_documents 的 GIN trgm 索引）
        db.session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        db.session.commit()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(autouse=True)
def _clear_email_code_store():
    """每个测试前清空邮箱验证码内存存储，防止冷却期跨测试泄漏。"""
    EmailCodeService._memory_store.clear()
    yield
    EmailCodeService._memory_store.clear()


@pytest.fixture
def auth_headers(client):
    """Register and login a test user, return auth headers."""
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    resp = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    data = resp.get_json()
    return {"Authorization": f"Bearer {data['access_token']}"}
