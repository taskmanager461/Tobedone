from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.models.goal import Goal
from backend.models.task import Task


def compute_goal_task_counts(db: Session, goal_ids: list[int]) -> dict[int, dict[str, int]]:
    if not goal_ids:
        return {}

    rows = (
        db.query(
            Task.goal_id,
            func.count(Task.id).label("total"),
            func.sum(case((Task.status == "completed", 1), else_=0)).label("completed"),
        )
        .filter(Task.goal_id.in_(goal_ids))
        .group_by(Task.goal_id)
        .all()
    )

    result: dict[int, dict[str, int]] = {}
    for goal_id, total, completed in rows:
        result[int(goal_id)] = {"total": int(total or 0), "completed": int(completed or 0)}
    return result


def calculate_pressure_status(goal: Goal, total_tasks: int, completed_tasks: int, today: date) -> str:
    if goal.status == "achieved":
        return "on_track"
    
    if goal.deadline < today:
        return "overdue"
    
    days_until_deadline = (goal.deadline - today).days
    progress = (completed_tasks / total_tasks) if total_tasks > 0 else 0.0
    
    goal_type = goal.goal_type
    risk_threshold_days = {
        "short_term": 1,
        "mid_term": 3,
        "long_term": 7
    }
    risk_threshold_progress = {
        "short_term": 0.5,
        "mid_term": 0.3,
        "long_term": 0.2
    }
    
    threshold_days = risk_threshold_days.get(goal_type, 3)
    threshold_progress = risk_threshold_progress.get(goal_type, 0.3)
    
    if days_until_deadline <= threshold_days and progress < threshold_progress:
        return "at_risk"
    
    return "on_track"


def refresh_goal_status(goal: Goal, total_tasks: int, completed_tasks: int) -> None:
    today = date.today()
    
    if goal.status == "active" and goal.deadline < today:
        goal.status = "failed"
        goal.completed_at = None
    elif goal.status == "achieved":
        pass
    
    goal.pressure_status = calculate_pressure_status(goal, total_tasks, completed_tasks, today)


def refresh_goal_status_by_id(db: Session, goal_id: int) -> None:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        return
    counts = compute_goal_task_counts(db, [goal.id]).get(goal.id, {"total": 0, "completed": 0})
    refresh_goal_status(goal, counts["total"], counts["completed"])


def get_days_remaining(goal: Goal, today: date) -> int | None:
    if goal.status == "achieved" or goal.status == "failed":
        return None
    delta = goal.deadline - today
    return max(0, delta.days)
