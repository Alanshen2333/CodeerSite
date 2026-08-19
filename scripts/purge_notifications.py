"""通知清理脚本 — 删除超过 90 天的通知。

用法：
    FLASK_ENV=development uv run python scripts/purge_notifications.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "api"))

from app import create_app
from app.services.notification_service import NotificationService


def main() -> None:
    app = create_app()
    with app.app_context():
        deleted = NotificationService.delete_expired()
        print(f"已清理 {deleted} 条过期通知。")


if __name__ == "__main__":
    main()
