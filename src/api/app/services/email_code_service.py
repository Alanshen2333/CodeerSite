import random
import string
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.extensions import mongo_db
from app.services.email_service import EmailService


class EmailCodeService:
    """邮箱验证码服务。

    - 验证码 6 位数字，默认 5 分钟有效。
    - 存储优先使用 MongoDB；Mongo 不可用时回退到进程内内存（仅开发/测试）。
    - 邮件发送支持 console（打印到日志）和 smtp 两种模式。
    """

    _memory_store: dict[str, dict] = {}

    @classmethod
    def _collection(cls):
        return mongo_db.codes if mongo_db is not None else None

    @classmethod
    def _key(cls, email: str, purpose: str) -> str:
        return f"email_code:{purpose}:{email.lower()}"

    @classmethod
    def _ttl_seconds(cls) -> int:
        return current_app.config.get("EMAIL_CODE_TTL", 300)

    @classmethod
    def _cooldown_seconds(cls) -> int:
        return current_app.config.get("EMAIL_CODE_COOLDOWN", 60)

    @classmethod
    def _generate_code(cls) -> str:
        return "".join(random.choices(string.digits, k=6))

    @classmethod
    def _store(cls, key: str, code: str, expires_at: datetime):
        now = datetime.now(timezone.utc)
        data = {"code": code, "expires_at": expires_at, "used": False, "sent_at": now}
        collection = cls._collection()
        if collection is not None:
            collection.replace_one(
                {"_id": key},
                {"_id": key, **data},
                upsert=True,
            )
        else:
            cls._memory_store[key] = data

    @classmethod
    def _fetch(cls, key: str) -> dict | None:
        collection = cls._collection()
        if collection is not None:
            doc = collection.find_one({"_id": key})
            if doc:
                doc.pop("_id", None)
            return doc
        return cls._memory_store.get(key)

    @classmethod
    def _mark_used(cls, key: str):
        collection = cls._collection()
        if collection is not None:
            collection.update_one({"_id": key}, {"$set": {"used": True}})
        elif key in cls._memory_store:
            cls._memory_store[key]["used"] = True

    @classmethod
    def send_code(cls, email: str, purpose: str) -> str:
        """生成验证码并发送邮件。返回发送的验证码（测试/调试用途）。

        同一 email+purpose 在冷却期（默认 60s）内不可重发，
        超出冷却期才允许再次发送。
        """
        key = cls._key(email, purpose)
        existing = cls._fetch(key)
        if existing and existing.get("sent_at"):
            cooldown = cls._cooldown_seconds()
            elapsed = (datetime.now(timezone.utc) - existing["sent_at"]).total_seconds()
            if elapsed < cooldown:
                raise ValueError(f"请 {int(cooldown - elapsed)} 秒后再试。")

        code = cls._generate_code()
        ttl = cls._ttl_seconds()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        cls._store(key, code, expires_at)

        subject = "Codeersite 验证码"
        body = f"你的验证码是：{code}，{ttl // 60} 分钟内有效。请勿泄露给他人。"
        EmailService.send(email, subject, body)
        return code

    @classmethod
    def verify_code(cls, email: str, purpose: str, code: str) -> bool:
        """验证验证码，验证成功后立即失效（一次性）。"""
        key = cls._key(email, purpose)
        record = cls._fetch(key)
        if record is None:
            return False
        if record.get("used"):
            return False
        if datetime.now(timezone.utc) > record["expires_at"]:
            return False
        if record["code"] != code:
            return False
        cls._mark_used(key)
        return True
