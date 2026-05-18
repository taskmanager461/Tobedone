from __future__ import annotations

from datetime import date
from typing import Iterable

from backend.models.task import Task

DIFFICULTY_WEIGHTS = {
    "easy": 5,
    "medium": 10,
    "hard": 20,
}


def get_multiplier(streak: int) -> float:
    if streak >= 7:
        return 1.2
    if streak >= 3:
        return 1.1
    return 1.0


def compute_task_reward(task: Task) -> float:
    base = DIFFICULTY_WEIGHTS.get(task.difficulty, 0)
    if task.status == "completed":
        return float(base)
    if task.status == "failed":
        return float(-0.5 * base)
    return 0.0


def compute_daily_metrics(tasks: Iterable[Task], current_streak: int) -> dict:
    tasks = list(tasks)
    total = len(tasks)
    if total == 0:
        return {
            "score": 0.0,
            "success_rate": 0.0,
            "total_tasks": 0,
            "multiplier": get_multiplier(current_streak),
            "completed_count": 0,
        }

    completed_count = sum(1 for t in tasks if t.status == "completed")
    success_rate = completed_count / total
    raw_score = sum(compute_task_reward(t) for t in tasks)
    multiplier = get_multiplier(current_streak)
    final_score = raw_score * multiplier

    return {
        "score": round(final_score, 2),
        "success_rate": round(success_rate, 4),
        "total_tasks": total,
        "multiplier": multiplier,
        "completed_count": completed_count,
    }


def compute_next_streak(success_rate: float, current_streak: int) -> int:
    if success_rate >= 0.7:
        return current_streak + 1
    if success_rate < 0.5:
        return 0
    return current_streak
