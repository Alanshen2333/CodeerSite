import random
import string
import uuid
from datetime import datetime, timezone, timedelta

from flask import current_app
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.extensions import db
from app.models.email_verification_code import EmailVerificationCode
from app.services.email_service import EmailService


class EmailCodeService:
    """邮箱验证码服务（PostgreSQL 存储）。

    - 验证码 6 位数字，默认 5 分钟有效。
    - email+purpose 唯一，重发时覆盖旧记录并重置 TTL。
    - 冷却期基于 sent_at 判断。
    - 消费时通过原子 UPDATE 抢占（used=false -> true），保证多 worker 下同一验证码只能成功一次。
    - 邮件发送支持 console（打印到日志）和 smtp 两种模式。
    """

    @classmethod
    def _key(cls, email: str, purpose: str) -> str:
        """兼容旧测试/调用的逻辑键。"""
        return f"email_code:{purpose}:{email.lower()}"

    @classmethod
    def _ttl_seconds(cls) -> int:
        return int(current_app.config.get("EMAIL_CODE_TTL", 300))

    @classmethod
    def _cooldown_seconds(cls) -> int:
        return int(current_app.config.get("EMAIL_CODE_COOLDOWN", 60))

    @classmethod
    def _generate_code(cls) -> str:
        return "".join(random.choices(string.digits, k=6))

    @classmethod
    def _get_record(cls, email: str, purpose: str) -> EmailVerificationCode | None:
        email_lower = email.lower()
        return db.session.execute(
            select(EmailVerificationCode).where(
                EmailVerificationCode.email == email_lower,
                EmailVerificationCode.purpose == purpose,
            )
        ).scalar_one_or_none()

    @classmethod
    def _upsert(cls, email: str, purpose: str, code: str, expires_at: datetime):
        email_lower = email.lower()
        sent_at = datetime.now(timezone.utc)
        stmt = pg_insert(EmailVerificationCode).values(
            id=str(uuid.uuid4()),
            email=email_lower,
            purpose=purpose,
            code=code,
            used=False,
            sent_at=sent_at,
            expires_at=expires_at,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_email_code_purpose",
            set_={
                "code": code,
                "used": False,
                "sent_at": sent_at,
                "expires_at": expires_at,
            },
        )
        db.session.execute(stmt)
        db.session.commit()

    @classmethod
    def send_code(cls, email: str, purpose: str) -> str:
        """生成验证码并发送邮件。返回发送的验证码（测试/调试用途）。

        同一 email+purpose 在冷却期（默认 60s）内不可重发，
        超出冷却期才允许再次发送。
        """
        existing = cls._get_record(email, purpose)
        if existing and existing.sent_at:
            cooldown = cls._cooldown_seconds()
            elapsed = (datetime.now(timezone.utc) - existing.sent_at).total_seconds()
            if elapsed < cooldown:
                raise ValueError(f"请 {int(cooldown - elapsed)} 秒后再试。")

        code = cls._generate_code()
        ttl = cls._ttl_seconds()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        cls._upsert(email, purpose, code, expires_at)

        subject = "Codeersite 验证码"
        body = f"你的验证码是：{code}，{ttl // 60} 分钟内有效。请勿泄露给他人。"
        EmailService.send(email, subject, body)
        return code

    @classmethod
    def verify_code(cls, email: str, purpose: str, code: str) -> bool:
        """验证验证码，验证成功后立即失效（一次性）。"""
        email_lower = email.lower()
        now = datetime.now(timezone.utc)
        stmt = (
            update(EmailVerificationCode)
            .where(
                EmailVerificationCode.email == email_lower,
                EmailVerificationCode.purpose == purpose,
                EmailVerificationCode.code == code,
                EmailVerificationCode.used.is_(False),
                EmailVerificationCode.expires_at > now,
            )
            .values(used=True)
        )
        result = db.session.execute(stmt)
        db.session.commit()
        return result.rowcount == 1
