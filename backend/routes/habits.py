from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.habit import Habit
from backend.models.habit_log import HabitLog
from backend.models.user import User
from backend.schemas import HabitCreate, HabitResponse, HabitTrackRequest
from backend.services.auth_service import get_current_user
from backend.services.habit_service import (
    compute_consistency_score,
    compute_streak_after_completion,
    decode_frequency_days,
    encode_frequency_days,
    has_missed_due_day_since_last_track,
    is_habit_due_on,
)
from backend.services.identity_service import apply_habit_impact

router = APIRouter(tags=["habits"])


@router.post("/habits", response_model=HabitResponse)
def create_habit(
    payload: HabitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.frequency_type == "weekly" and not payload.frequency_days:
        raise HTTPException(status_code=400, detail="frequency_days are required for weekly habits")
    if payload.frequency_type == "daily" and payload.frequency_days:
        raise HTTPException(status_code=400, detail="frequency_days can only be used for weekly habits")

    encoded_days = encode_frequency_days(payload.frequency_days)
    if payload.frequency_type == "weekly" and not encoded_days:
        raise HTTPException(status_code=400, detail="Weekly habits require valid days (0=Mon ... 6=Sun)")

    habit = Habit(
        user_id=current_user.id,
        title=payload.title.strip(),
        category=(payload.category or "general").strip().lower(),
        frequency_type=payload.frequency_type,
        frequency_days=encoded_days,
        preferred_time=payload.preferred_time,
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return HabitResponse(
        id=habit.id,
        title=habit.title,
        category=habit.category,
        frequency_type=habit.frequency_type,
        frequency_days=sorted(decode_frequency_days(habit.frequency_days)),
        preferred_time=habit.preferred_time,
        streak=habit.streak,
        best_streak=habit.best_streak,
        consistency_score=0.0,
        is_due_today=is_habit_due_on(habit, date.today()),
        today_status=None,
        is_active=habit.is_active,
        created_at=habit.created_at,
    )


@router.get("/habits", response_model=list[HabitResponse])
def list_habits(
    day: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_day = day or date.today()
    habits = (
        db.query(Habit)
        .filter(Habit.user_id == current_user.id, Habit.is_active.is_(True))
        .order_by(Habit.created_at.desc())
        .all()
    )
    if not habits:
        return []

    habit_ids = [habit.id for habit in habits]
    window_start = target_day - timedelta(days=29)
    logs = (
        db.query(HabitLog)
        .filter(HabitLog.user_id == current_user.id, HabitLog.habit_id.in_(habit_ids), HabitLog.date >= window_start, HabitLog.date <= target_day)
        .all()
    )
    logs_by_habit: dict[int, dict[date, HabitLog]] = {}
    for log in logs:
        logs_by_habit.setdefault(log.habit_id, {})[log.date] = log

    changed = False
    items: list[HabitResponse] = []
    for habit in habits:
        if has_missed_due_day_since_last_track(habit, target_day) and habit.streak != 0:
            habit.streak = 0
            changed = True
        habit_logs = logs_by_habit.get(habit.id, {})
        consistency_score = compute_consistency_score(habit, habit_logs, target_day)
        today_log = habit_logs.get(target_day)
        items.append(
            HabitResponse(
                id=habit.id,
                title=habit.title,
                category=habit.category,
                frequency_type=habit.frequency_type,
                frequency_days=sorted(decode_frequency_days(habit.frequency_days)),
                preferred_time=habit.preferred_time,
                streak=habit.streak,
                best_streak=habit.best_streak,
                consistency_score=consistency_score,
                is_due_today=is_habit_due_on(habit, target_day),
                today_status=today_log.status if today_log else None,
                is_active=habit.is_active,
                created_at=habit.created_at,
            )
        )

    if changed:
        db.commit()
    return items


@router.patch("/habits/{habit_id}/track")
def track_habit(
    habit_id: int,
    payload: HabitTrackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_day = payload.day or date.today()
    if target_day > date.today():
        raise HTTPException(status_code=400, detail="Cannot track future day")

    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == current_user.id, Habit.is_active.is_(True)).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if not is_habit_due_on(habit, target_day):
        raise HTTPException(status_code=400, detail="Habit is not scheduled for this day")

    if has_missed_due_day_since_last_track(habit, target_day):
        habit.streak = 0

    existing_log = (
        db.query(HabitLog)
        .filter(HabitLog.habit_id == habit.id, HabitLog.user_id == current_user.id, HabitLog.date == target_day)
        .first()
    )
    previous_status = existing_log.status if existing_log else None
    status_changed = previous_status != payload.status

    if not existing_log:
        existing_log = HabitLog(habit_id=habit.id, user_id=current_user.id, date=target_day, status=payload.status)
        db.add(existing_log)
    else:
        existing_log.status = payload.status

    # Keep streak independent from task streak and tuned for consistency.
    if status_changed:
        if payload.status == "completed":
            logs_window = (
                db.query(HabitLog)
                .filter(
                    HabitLog.habit_id == habit.id,
                    HabitLog.user_id == current_user.id,
                    HabitLog.date >= target_day - timedelta(days=40),
                    HabitLog.date <= target_day,
                )
                .all()
            )
            logs_by_day = {log.date: log for log in logs_window}
            logs_by_day[target_day] = existing_log
            habit.streak = compute_streak_after_completion(habit, logs_by_day, target_day)
            habit.best_streak = max(habit.best_streak, habit.streak)
        else:
            habit.streak = max(0, habit.streak - 1)

    if habit.last_tracked_on is None or target_day > habit.last_tracked_on:
        habit.last_tracked_on = target_day

    logs_for_consistency = (
        db.query(HabitLog)
        .filter(
            HabitLog.habit_id == habit.id,
            HabitLog.user_id == current_user.id,
            HabitLog.date >= target_day - timedelta(days=29),
            HabitLog.date <= target_day,
        )
        .all()
    )
    consistency_score = compute_consistency_score(habit, {log.date: log for log in logs_for_consistency}, target_day)

    progression = {"xp_delta": 0, "trust_delta": 0.0, "leveled_up": False}
    if status_changed:
        progression = apply_habit_impact(
            current_user,
            status=payload.status,
            consistency_score=consistency_score,
            habit_streak=habit.streak,
        )

    db.commit()
    return {
        "habit_id": habit.id,
        "date": target_day,
        "status": payload.status,
        "streak": habit.streak,
        "best_streak": habit.best_streak,
        "consistency_score": consistency_score,
        "identity_impact": progression,
    }
