import smtplib
from email.message import EmailMessage
from flask import current_app


class EmailService:
    """通用邮件发送服务。

    支持 console（开发环境，打印到日志）和 smtp（生产环境）两种驱动。
    配置从 Flask app.config 读取：
      MAIL_DRIVER          console|smtp（默认 console）
      MAIL_DEFAULT_SENDER  发件人地址
      MAIL_SERVER          SMTP 服务器（默认 localhost）
      MAIL_PORT            SMTP 端口（默认 587）
      MAIL_USERNAME        SMTP 用户名
      MAIL_PASSWORD        SMTP 密码
      MAIL_USE_TLS         是否启用 TLS（默认 true）
    """

    @classmethod
    def send(cls, to: str, subject: str, body: str):
        """发送邮件，根据 MAIL_DRIVER 选择投递方式。"""
        driver = current_app.config.get("MAIL_DRIVER", "console").lower()
        sender = current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@codeer.site")

        if driver == "console":
            current_app.logger.info(
                "[EMAIL] to=%s subject=%s", to, subject
            )
            return

        if driver == "smtp":
            msg = EmailMessage()
            msg["From"] = sender
            msg["To"] = to
            msg["Subject"] = subject
            msg.set_content(body)

            server = current_app.config.get("MAIL_SERVER", "localhost")
            port = current_app.config.get("MAIL_PORT", 587)
            username = current_app.config.get("MAIL_USERNAME")
            password = current_app.config.get("MAIL_PASSWORD")
            use_tls = current_app.config.get("MAIL_USE_TLS", True)

            with smtplib.SMTP(server, port) as smtp:
                if use_tls:
                    smtp.starttls()
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(msg)
            return

        raise RuntimeError(f"Unsupported MAIL_DRIVER: {driver}")
