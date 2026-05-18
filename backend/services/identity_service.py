from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from backend.models.goal import Goal
from backend.models.task import Task
from backend.models.user import User

TASK_XP_BY_DIFFICULTY = {"easy": 8, "medium": 12, "hard": 18}
TASK_PRIORITY_MULTIPLIER = {"low": 1.0, "medium": 1.1, "high": 1.2}
GOAL_XP_BY_TYPE = {
    "today": 70,
    "tomorrow": 80,
    "three_days": 85,
    "one_week": 95,
    "two_weeks": 105,
    "one_month": 120,
    "three_months": 140,
    "six_months": 155,
    "one_year": 175,
    "one_year_plus": 190,
}

BADGE_DEFINITIONS = [
    {"id": "first_task_completed", "label": "First Task Completed"},
    {"id": "first_goal_completed", "label": "First Goal Completed"},
    {"id": "streak_7", "label": "7 Day Streak"},
    {"id": "goal_crusher", "label": "Goal Crusher"},
]


def xp_required_for_level(level: int) -> int:
    if level <= 1:
        return 0
    required = 0
    for lvl in range(1, level):
        required += 100 + (lvl - 1) * 40
    return required


def compute_level_from_xp(total_xp: int) -> int:
    level = 1
    while total_xp >= xp_required_for_level(level + 1):
        level += 1
    return level


def _streak_multiplier(streak: int, cap: int = 14, step: float = 0.02) -> float:
    return 1.0 + min(streak, cap) * step


def _trust_anchor(total_xp: int, level: int) -> float:
    anchor = 18.0 + (level * 3.0) + min(42.0, total_xp / 55.0)
    return max(0.0, min(100.0, anchor))


def _trust_gain_from_xp(xp_delta: int, is_goal: bool = False) -> float:
    gain = min(2.5, xp_delta * 0.04)
    if is_goal:
        gain += 1.5
    return gain


def recompute_streak(db: Session, user: User, today: date | None = None) -> int:
    today = today or date.today()
    completed_dates = {
        task_date
        for (task_date,) in db.query(Task.date)
        .filter(Task.user_id == user.id, Task.status == "completed")
        .distinct()
        .all()
    }
    if not completed_dates:
        user.streak = 0
        return 0

    if today not in completed_dates and (today - timedelta(days=1)) not in completed_dates:
        user.streak = 0
        return 0

    cursor = today if today in completed_dates else today - timedelta(days=1)
    streak = 0
    while cursor in completed_dates:
        streak += 1
        cursor -= timedelta(days=1)
    user.streak = streak
    return streak


def _apply_progression_gain(user: User, xp_delta: int, is_goal: bool) -> dict:
    xp_delta = max(0, xp_delta)
    previous_level = max(1, user.level or 1)
    user.total_xp = max(0, (user.total_xp or 0) + xp_delta)
    user.level = compute_level_from_xp(user.total_xp)
    anchor = _trust_anchor(user.total_xp, user.level)
    trust_boost = _trust_gain_from_xp(xp_delta, is_goal=is_goal)
    user.trust_score = min(100.0, max(anchor * 0.35, (user.trust_score or 0.0) + trust_boost))
    return {
        "xp_delta": xp_delta,
        "previous_level": previous_level,
        "current_level": user.level,
        "leveled_up": user.level > previous_level,
    }


def award_task_completion_xp(db: Session, user: User, task: Task) -> dict:
    streak = recompute_streak(db, user)
    base_xp = TASK_XP_BY_DIFFICULTY.get(task.difficulty, 10)
    priority_multiplier = TASK_PRIORITY_MULTIPLIER.get(task.priority, 1.0)
    streak_multiplier = _streak_multiplier(streak, step=0.02)
    xp_delta = int(round(base_xp * priority_multiplier * streak_multiplier))
    return _apply_progression_gain(user, xp_delta=xp_delta, is_goal=False)


def award_goal_completion_xp(db: Session, user: User, goal: Goal) -> dict:
    streak = recompute_streak(db, user)
    base_xp = GOAL_XP_BY_TYPE.get(goal.goal_type, 100)
    deadline_bonus = 0
    if goal.completed_at:
        if goal.completed_at.date() < goal.deadline:
            deadline_bonus = 20
        elif goal.completed_at.date() == goal.deadline:
            deadline_bonus = 8
    streak_multiplier = _streak_multiplier(streak, step=0.015)
    xp_delta = int(round((base_xp + deadline_bonus) * streak_multiplier))
    return _apply_progression_gain(user, xp_delta=xp_delta, is_goal=True)


def apply_habit_impact(user: User, status: str, consistency_score: float, habit_streak: int) -> dict:
    if status == "completed":
        xp_delta = 4
        if consistency_score >= 70:
            xp_delta += 1
        if habit_streak >= 7:
            xp_delta += 1
        progression = _apply_progression_gain(user, xp_delta=xp_delta, is_goal=False)
        trust_boost = 0.25 + min(0.9, consistency_score * 0.007)
        if habit_streak >= 10:
            trust_boost += 0.2
        user.trust_score = min(150.0, (user.trust_score or 0.0) + trust_boost)
        return {
            "xp_delta": progression["xp_delta"],
            "trust_delta": round(trust_boost, 2),
            "leveled_up": progression["leveled_up"],
        }

    trust_penalty = 0.1
    if consistency_score < 40:
        trust_penalty = 0.35
    elif consistency_score < 60:
        trust_penalty = 0.2
    user.trust_score = max(0.0, (user.trust_score or 0.0) - trust_penalty)
    return {"xp_delta": 0, "trust_delta": -round(trust_penalty, 2), "leveled_up": False}


def build_badges(completed_tasks: int, completed_goals: int, streak: int) -> list[dict]:
    unlocked_ids: set[str] = set()
    if completed_tasks >= 1:
        unlocked_ids.add("first_task_completed")
    if completed_goals >= 1:
        unlocked_ids.add("first_goal_completed")
    if streak >= 7:
        unlocked_ids.add("streak_7")
    if completed_goals >= 5:
        unlocked_ids.add("goal_crusher")
    return [
        {"id": badge["id"], "label": badge["label"], "unlocked": badge["id"] in unlocked_ids}
        for badge in BADGE_DEFINITIONS
    ]


def get_identity_profile(db: Session, user: User) -> dict:
    completed_tasks = db.query(Task).filter(Task.user_id == user.id, Task.status == "completed").count()
    completed_goals = db.query(Goal).filter(Goal.user_id == user.id, Goal.status == "achieved").count()

    recompute_streak(db, user)
    computed_level = compute_level_from_xp(user.total_xp or 0)
    if computed_level != user.level:
        user.level = computed_level

    trust_anchor = _trust_anchor(user.total_xp or 0, user.level or 1)
    if (user.trust_score or 0.0) < trust_anchor * 0.2:
        user.trust_score = trust_anchor * 0.2

    current_level = max(1, user.level or 1)
    current_level_floor = xp_required_for_level(current_level)
    next_level = current_level + 1
    next_level_xp = xp_required_for_level(next_level)
    xp_in_level = max(0, (user.total_xp or 0) - current_level_floor)
    level_span = max(1, next_level_xp - current_level_floor)
    progress_percent = round((xp_in_level / level_span) * 100, 1)
    badges = build_badges(completed_tasks, completed_goals, user.streak)

    db.commit()
    return {
        "level": current_level,
        "total_xp": user.total_xp or 0,
        "next_level": next_level,
        "next_level_xp": next_level_xp,
        "xp_into_current_level": xp_in_level,
        "xp_for_next_level": level_span,
        "level_progress_percent": progress_percent,
        "trust_score": round(user.trust_score or 0.0, 2),
        "completed_tasks": completed_tasks,
        "completed_goals": completed_goals,
        "streak": user.streak,
        "badges": badges,
    }
