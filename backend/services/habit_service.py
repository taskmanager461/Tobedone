from __future__ import annotations

from datetime import date, timedelta

from backend.models.habit import Habit
from backend.models.habit_log import HabitLog


def decode_frequency_days(raw_days: str | None) -> set[int]:
    if not raw_days:
        return set()
    values: set[int] = set()
    for token in raw_days.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            day_value = int(token)
        except ValueError:
            continue
        if 0 <= day_value <= 6:
            values.add(day_value)
    return values


def encode_frequency_days(days: list[int] | None) -> str | None:
    if not days:
        return None
    normalized = sorted({d for d in days if 0 <= d <= 6})
    if not normalized:
        return None
    return ",".join(str(d) for d in normalized)


def is_habit_due_on(habit: Habit, day: date) -> bool:
    if not habit.is_active:
        return False
    if habit.frequency_type == "daily":
        return True
    days = decode_frequency_days(habit.frequency_days)
    return day.weekday() in days


def due_days_between(habit: Habit, start_day: date, end_day: date) -> list[date]:
    if end_day < start_day:
        return []
    out: list[date] = []
    cursor = start_day
    while cursor <= end_day:
        if is_habit_due_on(habit, cursor):
            out.append(cursor)
        cursor += timedelta(days=1)
    return out


def has_missed_due_day_since_last_track(habit: Habit, today: date) -> bool:
    if not habit.last_tracked_on:
        return False
    start_day = habit.last_tracked_on + timedelta(days=1)
    end_day = today - timedelta(days=1)
    if end_day < start_day:
        return False
    return len(due_days_between(habit, start_day, end_day)) > 0


def compute_consistency_score(habit: Habit, logs_by_day: dict[date, HabitLog], today: date, window_days: int = 30) -> float:
    start_day = today - timedelta(days=max(1, window_days) - 1)
    due_days = due_days_between(habit, start_day, today)
    if not due_days:
        return 0.0
    completed_count = 0
    for due_day in due_days:
        log = logs_by_day.get(due_day)
        if log and log.status == "completed":
            completed_count += 1
    return round((completed_count / len(due_days)) * 100, 1)


def compute_streak_after_completion(habit: Habit, logs_by_day: dict[date, HabitLog], track_day: date) -> int:
    previous_due_day = track_day - timedelta(days=1)
    while previous_due_day >= (habit.created_at.date() if habit.created_at else previous_due_day):
        if is_habit_due_on(habit, previous_due_day):
            break
        previous_due_day -= timedelta(days=1)
    previous_log = logs_by_day.get(previous_due_day)
    if previous_log and previous_log.status == "completed":
        return max(1, habit.streak + 1)
    return 1
