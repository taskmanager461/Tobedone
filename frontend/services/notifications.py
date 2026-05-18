from __future__ import annotations

from datetime import date, datetime
from typing import Any


def build_time_notifications(
    tasks: list[dict[str, Any]],
    score: dict[str, Any],
    last_daily_summary: str,
    t: Any,
) -> tuple[list[tuple[str, str]], str]:
    notifications: list[tuple[str, str]] = []
    now = datetime.now()
    pending = sum(1 for task in tasks if task.get("status") == "pending")
    completed = sum(1 for task in tasks if task.get("status") == "completed")

    if now.hour < 12 and pending > 0:
        notifications.append(("info", t("notif_start_reminder", count=str(pending))))
    if now.hour >= 18 and pending > 0:
        notifications.append(("warning", t("notif_end_reminder", count=str(pending))))

    today_key = date.today().isoformat()
    if last_daily_summary != today_key:
        notifications.append(
            (
                "summary",
                t(
                    "notif_daily_summary",
                    completed=str(completed),
                    total=str(len(tasks)),
                    score=f"{float(score.get('score', 0.0)):.1f}",
                ),
            )
        )
        return notifications, today_key

    return notifications, last_daily_summary
