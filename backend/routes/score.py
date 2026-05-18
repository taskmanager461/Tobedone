from datetime import date, timedelta
from collections import defaultdict
from time import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.daily_score import DailyScore
from backend.models.goal import Goal
from backend.models.habit import Habit
from backend.models.habit_log import HabitLog
from backend.models.task import Task
from backend.models.user import User
from backend.schemas import DailyScoreComputationResponse, DailyScoreRequest, DailyScoreResponse
from backend.services.auth_service import get_current_user
from backend.services.goal_service import compute_goal_task_counts, refresh_goal_status
from backend.services.habit_service import compute_consistency_score, is_habit_due_on
from backend.services.identity_service import recompute_streak

router = APIRouter(tags=["score"])
SMART_INSIGHTS_CACHE: dict[int, dict] = {}
SMART_CACHE_TTL_SECONDS = 300


@router.post("/score/daily", response_model=DailyScoreComputationResponse)
def compute_daily_score(
    payload: DailyScoreRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_user_id = payload.user_id or current_user.id
    if target_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    day = payload.day or date.today()
    
    current_streak = recompute_streak(db, current_user, today=day)

    tasks = db.query(Task).filter(Task.user_id == target_user_id, Task.date == day).all()
    if not tasks:
        goal_bonus = 0.0
        completed_goals_today = db.query(Goal).filter(
            Goal.user_id == target_user_id,
            Goal.status == "achieved",
            func.date(Goal.completed_at) == day,
        ).all()
        for goal in completed_goals_today:
            goal_bonus += 30.0
            if goal.completed_at and goal.completed_at.date() < goal.deadline:
                goal_bonus += 15.0
            elif goal.completed_at and goal.completed_at.date() == goal.deadline:
                goal_bonus += 5.0
        
        failed_goals_today = db.query(Goal).filter(
            Goal.user_id == target_user_id,
            Goal.status == "failed",
            (func.date(Goal.deadline) == day) | (func.date(Goal.completed_at) == day),
        ).all()
        for goal in failed_goals_today:
            goal_bonus -= 25.0

        level = max(1, current_user.level or 1)
        stability = min(0.82, 0.35 + level * 0.03)
        xp_factor = min(18.0, (current_user.total_xp or 0) / 120.0)
        level_factor = level * 1.2
        current_user.trust_score = max(
            0.0,
            min(
                150.0,
                ((current_user.trust_score or 0.0) * stability) + (goal_bonus * (1 - stability)) + xp_factor + level_factor,
            ),
        )

        db.commit()
        return DailyScoreComputationResponse(
            date=day,
            score=round(current_user.trust_score, 2),
            success_rate=0.0,
            streak=current_streak,
            multiplier=1.0,
            total_tasks=0,
            goal_bonus=goal_bonus,
        )

    # 2. Compute Score with Difficulty & Priority weights
    difficulty_map = {"easy": 1, "medium": 2, "hard": 3}
    priority_map = {"low": 1, "medium": 1.5, "high": 2}
    
    total_weight = 0
    earned_weight = 0
    completed_count = 0

    for task in tasks:
        weight = difficulty_map.get(task.difficulty, 1) * priority_map.get(task.priority, 1)
        total_weight += weight
        if task.status == "completed":
            earned_weight += weight
            completed_count += 1

    success_rate = completed_count / len(tasks) if len(tasks) > 0 else 0.0
    
    # Streak multiplier (bonus only, not primary source)
    multiplier = 1.0 + (min(current_streak, 10) * 0.1)
    base_score = (earned_weight / total_weight) * 100 if total_weight > 0 else 0
    final_score = base_score * multiplier

    # Goals have stronger trust-score impact than regular tasks - MUCH HIGHER WEIGHT!
    goal_bonus = 0.0
    
    # Completed goals - BIG boost!
    completed_goals_today = db.query(Goal).filter(
        Goal.user_id == target_user_id,
        Goal.status == "achieved",
        func.date(Goal.completed_at) == day,
    ).all()
    for goal in completed_goals_today:
        goal_bonus += 30.0
        if goal.completed_at and goal.completed_at.date() < goal.deadline:
            goal_bonus += 15.0
        elif goal.completed_at and goal.completed_at.date() == goal.deadline:
            goal_bonus += 5.0
    
    # Failed goals - Penalty!
    failed_goals_today = db.query(Goal).filter(
        Goal.user_id == target_user_id,
        Goal.status == "failed",
        (func.date(Goal.deadline) == day) | (func.date(Goal.completed_at) == day),
    ).all()
    for goal in failed_goals_today:
        goal_bonus -= 25.0

    performance_score = max(0.0, final_score + goal_bonus)
    level = max(1, current_user.level or 1)
    stability = min(0.82, 0.35 + level * 0.03)
    xp_factor = min(18.0, (current_user.total_xp or 0) / 120.0)
    level_factor = level * 1.2
    trust_delta_from_goals = 0.0
    if goal_bonus > 0:
        trust_delta_from_goals = min(5.0, goal_bonus * 0.08)
    elif goal_bonus < 0:
        trust_delta_from_goals = max(-4.0, goal_bonus * 0.06)
    stabilized_trust = (
        ((current_user.trust_score or 0.0) * stability)
        + (performance_score * (1 - stability))
        + xp_factor
        + level_factor
        + trust_delta_from_goals
    )
    current_user.trust_score = max(0.0, min(150.0, stabilized_trust))

    # 4. Save/Update DailyScore
    daily_score = db.query(DailyScore).filter(DailyScore.user_id == target_user_id, DailyScore.date == day).first()
    if not daily_score:
        daily_score = DailyScore(user_id=target_user_id, date=day, score=current_user.trust_score, success_rate=success_rate)
        db.add(daily_score)
    else:
        daily_score.score = current_user.trust_score
        daily_score.success_rate = success_rate

    db.commit()

    return DailyScoreComputationResponse(
        date=day,
        score=round(current_user.trust_score, 2),
        success_rate=success_rate,
        streak=current_streak,
        multiplier=multiplier,
        total_tasks=len(tasks),
        goal_bonus=goal_bonus,
    )


@router.get("/score/history", response_model=list[DailyScoreResponse])
def score_history(
    user_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_user_id = user_id or current_user.id
    if target_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    records = (
        db.query(DailyScore)
        .filter(DailyScore.user_id == target_user_id)
        .order_by(DailyScore.date.asc())
        .all()
    )
    return records


@router.get("/score/weekly-summary")
def weekly_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    prev_week_start = week_start - timedelta(days=7)
    prev_week_end = prev_week_start + timedelta(days=6)
    
    # Current week tasks
    current_tasks = db.query(Task).filter(
        Task.user_id == current_user.id,
        Task.date >= week_start,
        Task.date <= week_end
    ).all()
    
    # Previous week tasks
    prev_tasks = db.query(Task).filter(
        Task.user_id == current_user.id,
        Task.date >= prev_week_start,
        Task.date <= prev_week_end
    ).all()
    
    current_total = len(current_tasks)
    current_completed = sum(1 for t in current_tasks if t.status == "completed")
    current_success = (current_completed / current_total) * 100 if current_total > 0 else 0
    
    prev_total = len(prev_tasks)
    prev_completed = sum(1 for t in prev_tasks if t.status == "completed")
    prev_success = (prev_completed / prev_total) * 100 if prev_total > 0 else 0
    
    success_change = 0
    if prev_success > 0:
        success_change = ((current_success - prev_success) / prev_success) * 100
    
    return {
        "current_week": {
            "total_tasks": current_total,
            "completed_tasks": current_completed,
            "success_rate": round(current_success, 1),
            "streak": current_user.streak
        },
        "previous_week": {
            "total_tasks": prev_total,
            "completed_tasks": prev_completed,
            "success_rate": round(prev_success, 1)
        },
        "success_change": round(success_change, 1)
    }


@router.get("/insights/smart")
def smart_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Build fast signature for lightweight cache invalidation.
    task_signature = db.query(
        func.count(Task.id),
        func.sum(case((Task.status == "completed", 1), else_=0)),
        func.sum(case((Task.status == "failed", 1), else_=0)),
        func.max(Task.id),
    ).filter(Task.user_id == current_user.id).first()
    goal_signature = db.query(
        func.count(Goal.id),
        func.sum(case((Goal.status == "achieved", 1), else_=0)),
        func.sum(case((Goal.status == "failed", 1), else_=0)),
        func.max(Goal.id),
    ).filter(Goal.user_id == current_user.id).first()
    habit_signature = db.query(
        func.count(Habit.id),
        func.max(Habit.id),
    ).filter(Habit.user_id == current_user.id, Habit.is_active.is_(True)).first()
    habit_log_signature = db.query(
        func.count(HabitLog.id),
        func.sum(case((HabitLog.status == "completed", 1), else_=0)),
        func.sum(case((HabitLog.status == "skipped", 1), else_=0)),
        func.max(HabitLog.id),
    ).filter(HabitLog.user_id == current_user.id).first()
    signature = (
        int(task_signature[0] or 0),
        int(task_signature[1] or 0),
        int(task_signature[2] or 0),
        int(task_signature[3] or 0),
        int(goal_signature[0] or 0),
        int(goal_signature[1] or 0),
        int(goal_signature[2] or 0),
        int(goal_signature[3] or 0),
        int(habit_signature[0] or 0),
        int(habit_signature[1] or 0),
        int(habit_log_signature[0] or 0),
        int(habit_log_signature[1] or 0),
        int(habit_log_signature[2] or 0),
        int(habit_log_signature[3] or 0),
        int(current_user.streak or 0),
        str(date.today()),
    )
    cached = SMART_INSIGHTS_CACHE.get(current_user.id)
    if cached and cached.get("signature") == signature and (time() - cached.get("timestamp", 0)) < SMART_CACHE_TTL_SECONDS:
        return cached["payload"]

    all_tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    user_goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    habits = db.query(Habit).filter(Habit.user_id == current_user.id, Habit.is_active.is_(True)).all()
    counts_map = compute_goal_task_counts(db, [g.id for g in user_goals])

    if not all_tasks and not user_goals and not habits:
        payload = {
            "productive_hour": None,
            "failure_hour": None,
            "productive_day": None,
            "productive_window": None,
            "failure_window": None,
            "consistency_score": 0.0,
            "pressure_level": "light",
            "insights": [],
            "suggestions": [],
            "for_you": [],
            "adaptive_feedback": [],
            "goal_completion_rate": 0.0,
            "goals_achieved": 0,
            "goals_failed": 0,
            "average_completion_time": 0.0,
            "habit_insights": [],
            "best_habits": [],
            "worst_habits": [],
            "failure_analysis": {
                "top_failure_categories": [],
                "failure_hours": [],
                "failure_days": []
            },
            "success_analysis": {
                "top_success_categories": [],
                "success_hours": [],
                "success_days": []
            },
            "goal_analysis": {
                "short_term_success": 0.0,
                "long_term_success": 0.0,
                "avg_completion_short": 0.0,
                "avg_completion_long": 0.0
            },
            "category_analysis": [],
            "weekly_comparison": None
        }
        SMART_INSIGHTS_CACHE[current_user.id] = {"signature": signature, "timestamp": time(), "payload": payload}
        return payload

    # --- FAILURE ANALYSIS ---
    completed_by_hour = defaultdict(int)
    failed_by_hour = defaultdict(int)
    completed_by_day = defaultdict(int)
    failed_by_day = defaultdict(int)
    completed_by_category = defaultdict(int)
    failed_by_category = defaultdict(int)
    total_by_category = defaultdict(int)
    active_days: dict[date, bool] = {}

    completed_tasks = 0
    failed_tasks = 0
    for task in all_tasks:
        total_by_category[task.category] += 1
        if task.status == "completed":
            completed_tasks += 1
            completed_by_category[task.category] += 1
        elif task.status == "failed":
            failed_tasks += 1
            failed_by_category[task.category] += 1
        if task.status in {"completed", "failed"}:
            active_days[task.date] = True

        if task.time:
            try:
                hour = int(task.time.split(":")[0])
                if task.status == "completed":
                    completed_by_hour[hour] += 1
                elif task.status == "failed":
                    failed_by_hour[hour] += 1
            except (ValueError, IndexError):
                pass
        
        if task.date:
            if task.status == "completed":
                completed_by_day[task.date.weekday()] += 1
            elif task.status == "failed":
                failed_by_day[task.date.weekday()] += 1

    # Calculate failure rates per category
    category_failure_rates = []
    for category, total in total_by_category.items():
        if total >= 3:
            failure_rate = failed_by_category.get(category, 0) / total
            category_failure_rates.append((category, failure_rate, total))
    category_failure_rates.sort(key=lambda x: -x[1])

    # --- SUCCESS ANALYSIS ---
    category_success_rates = []
    for category, total in total_by_category.items():
        if total >= 3:
            success_rate = completed_by_category.get(category, 0) / total
            category_success_rates.append((category, success_rate, total))
    category_success_rates.sort(key=lambda x: -x[1])

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    productive_hour = max(completed_by_hour, key=completed_by_hour.get) if completed_by_hour else None
    failure_hour = max(failed_by_hour, key=failed_by_hour.get) if failed_by_hour else None
    productive_day_index = max(completed_by_day, key=completed_by_day.get) if completed_by_day else None
    productive_day = day_names[productive_day_index] if productive_day_index is not None else None

    def _hour_window(hour: int | None) -> str | None:
        if hour is None:
            return None
        start = max(0, hour - 1)
        end = min(23, hour + 2)
        return f"{start:02d}:00-{end:02d}:00"

    productive_window = _hour_window(productive_hour)
    failure_window = _hour_window(failure_hour)

    total_outcomes = completed_tasks + failed_tasks
    success_ratio = (completed_tasks / total_outcomes) if total_outcomes > 0 else 0.0
    failure_ratio = (failed_tasks / total_outcomes) if total_outcomes > 0 else 0.0

    day_span = max(1, (date.today() - min(active_days.keys())).days + 1) if active_days else 1
    activity_ratio = min(1.0, len(active_days) / day_span)
    streak_factor = min(1.0, (current_user.streak or 0) / 14.0)
    consistency_score = round(((activity_ratio * 0.45) + (success_ratio * 0.40) + (streak_factor * 0.15)) * 100, 1)

    for goal in user_goals:
        counts = counts_map.get(goal.id, {"total": 0, "completed": 0})
        refresh_goal_status(goal, counts["total"], counts["completed"])
    db.commit()

    # --- GOAL ANALYSIS ---
    goals_achieved = sum(1 for g in user_goals if g.status == "achieved")
    goals_failed = sum(1 for g in user_goals if g.status == "failed")
    goal_completion_rate = (goals_achieved / len(user_goals) * 100) if user_goals else 0.0

    short_term_goals = []
    long_term_goals = []
    completion_samples = []
    for g in user_goals:
        target_days = max(1, (g.deadline - g.created_at.date()).days)
        if g.status == "achieved" and g.completed_at:
            duration = max(0, (g.completed_at.date() - g.created_at.date()).days)
            completion_samples.append(duration)
            if target_days <= 14:
                short_term_goals.append({"status": "achieved", "duration": duration})
            else:
                long_term_goals.append({"status": "achieved", "duration": duration})
        elif g.status == "failed":
            if target_days <= 14:
                short_term_goals.append({"status": "failed"})
            else:
                long_term_goals.append({"status": "failed"})

    short_term_achieved = sum(1 for g in short_term_goals if g["status"] == "achieved")
    long_term_achieved = sum(1 for g in long_term_goals if g["status"] == "achieved")
    short_term_success = (short_term_achieved / len(short_term_goals) * 100) if short_term_goals else 0.0
    long_term_success = (long_term_achieved / len(long_term_goals) * 100) if long_term_goals else 0.0

    avg_completion_short = sum(g["duration"] for g in short_term_goals if g["status"] == "achieved") / short_term_achieved if short_term_achieved else 0
    avg_completion_long = sum(g["duration"] for g in long_term_goals if g["status"] == "achieved") / long_term_achieved if long_term_achieved else 0
    avg_completion_days = round((sum(completion_samples) / len(completion_samples)), 1) if completion_samples else 0.0

    # --- HABIT ANALYSIS ---
    today = date.today()
    habit_insights: list[str] = []
    best_habits: list[dict] = []
    worst_habits: list[dict] = []
    if habits:
        habit_ids = [h.id for h in habits]
        habit_logs = (
            db.query(HabitLog)
            .filter(
                HabitLog.user_id == current_user.id,
                HabitLog.habit_id.in_(habit_ids),
                HabitLog.date >= today - timedelta(days=59),
                HabitLog.date <= today,
            )
            .all()
        )
        logs_by_habit: dict[int, dict[date, HabitLog]] = defaultdict(dict)
        for log in habit_logs:
            logs_by_habit[log.habit_id][log.date] = log

        habit_scores: list[tuple[Habit, float]] = []
        for habit in habits:
            consistency = compute_consistency_score(habit, logs_by_habit.get(habit.id, {}), today, window_days=30)
            habit_scores.append((habit, consistency))
            if consistency >= 75:
                best_habits.append({"title": habit.title, "consistency": consistency})
            if consistency <= 45:
                worst_habits.append({"title": habit.title, "consistency": consistency})

            weekend_due = 0
            weekend_skips = 0
            for days_back in range(14):
                day = today - timedelta(days=days_back)
                if day.weekday() not in (5, 6):
                    continue
                if not is_habit_due_on(habit, day):
                    continue
                weekend_due += 1
                log = logs_by_habit.get(habit.id, {}).get(day)
                if log and log.status == "skipped":
                    weekend_skips += 1
            if weekend_due >= 3 and weekend_skips / weekend_due >= 0.6:
                habit_insights.append(f"You skip '{habit.title}' more often on weekends")

        habit_scores.sort(key=lambda item: item[1], reverse=True)
        if habit_scores:
            top_habit, top_score = habit_scores[0]
            habit_insights.append(f"Best performing habit: {top_habit.title} ({top_score:.0f}% consistency)")
        if len(habit_scores) > 1:
            low_habit, low_score = habit_scores[-1]
            habit_insights.append(f"Needs attention: {low_habit.title} ({low_score:.0f}% consistency)")

    short_term_samples: list[int] = []
    long_term_samples: list[int] = []
    long_term_failed = 0
    for g in user_goals:
        target_days = max(1, (g.deadline - g.created_at.date()).days)
        if g.status == "failed" and target_days >= 30:
            long_term_failed += 1
        if g.status != "achieved" or not g.completed_at:
            continue
        duration = max(0, (g.completed_at.date() - g.created_at.date()).days)
        if target_days <= 14:
            short_term_samples.append(duration)
        if target_days >= 30:
            long_term_samples.append(duration)

    pressure_level = "normal"
    if failure_ratio >= 0.45 or consistency_score < 42:
        pressure_level = "light"
    elif failure_ratio <= 0.2 and consistency_score >= 68:
        pressure_level = "high"

    insights: list[str] = []
    if productive_window:
        insights.append(f"You are most productive between {productive_window}")
    if failure_window:
        insights.append(f"You tend to fail tasks around {failure_window}")
    if productive_day:
        insights.append(f"Your best day is {productive_day}")
    if consistency_score >= 70:
        insights.append("You are building strong consistency")
    elif consistency_score < 40 and total_outcomes >= 6:
        insights.append("Your consistency is unstable this period")
    insights.extend(habit_insights[:2])

    suggestions: list[str] = []
    if productive_window:
        suggestions.append(f"Try scheduling priority tasks in {productive_window}")
    if failure_window:
        suggestions.append("Avoid packing heavy tasks in your failure-prone hours")
    if short_term_samples and long_term_samples and (sum(short_term_samples) / len(short_term_samples)) < (sum(long_term_samples) / len(long_term_samples)):
        suggestions.append("You perform better with short-term goals")
    if long_term_failed >= 2:
        suggestions.append("Try breaking long-term goals into smaller milestones")
    if pressure_level == "light":
        suggestions.append("Keep task load moderate and focus on steady wins")
    elif pressure_level == "high":
        suggestions.append("You can handle a more demanding plan this week")

    adaptive_feedback: list[str] = []
    if long_term_failed >= 2:
        adaptive_feedback.append("Try breaking goals into smaller parts")
    if consistency_score >= 65:
        adaptive_feedback.append("You are improving your consistency")

    for_you = (insights + suggestions + adaptive_feedback)[:4]
    if len(for_you) < 2:
        for_you.extend(["Keep tracking progress daily for sharper personalization"])
    for_you = for_you[:4]

    # --- CATEGORY ANALYSIS ---
    category_analysis = []
    for cat, success_rate, total in category_success_rates:
        category_analysis.append({
            "category": cat,
            "total": total,
            "success_rate": round(success_rate * 100, 1),
            "failure_rate": round((1 - success_rate) * 100, 1)
        })
    for cat, failure_rate, total in category_failure_rates:
        if not any(a["category"] == cat for a in category_analysis):
            category_analysis.append({
                "category": cat,
                "total": total,
                "success_rate": round((1 - failure_rate) * 100, 1),
                "failure_rate": round(failure_rate * 100, 1)
            })

    payload = {
        "productive_hour": productive_hour,
        "failure_hour": failure_hour,
        "productive_day": productive_day,
        "productive_window": productive_window,
        "failure_window": failure_window,
        "consistency_score": consistency_score,
        "pressure_level": pressure_level,
        "insights": insights,
        "suggestions": suggestions,
        "for_you": for_you,
        "adaptive_feedback": adaptive_feedback,
        "goal_completion_rate": round(goal_completion_rate, 1),
        "goals_achieved": goals_achieved,
        "goals_failed": goals_failed,
        "average_completion_time": avg_completion_days,
        "habit_insights": habit_insights,
        "best_habits": best_habits,
        "worst_habits": worst_habits,
        "failure_analysis": {
            "top_failure_categories": [{"category": cat, "rate": round(rate*100,1)} for cat, rate, _ in category_failure_rates[:5]],
            "failure_hours": sorted(failed_by_hour.items(), key=lambda x: -x[1])[:5],
            "failure_days": [{"day": day_names[d], "count": c} for d, c in sorted(failed_by_day.items(), key=lambda x: -x[1])[:5]]
        },
        "success_analysis": {
            "top_success_categories": [{"category": cat, "rate": round(rate*100,1)} for cat, rate, _ in category_success_rates[:5]],
            "success_hours": sorted(completed_by_hour.items(), key=lambda x: -x[1])[:5],
            "success_days": [{"day": day_names[d], "count": c} for d, c in sorted(completed_by_day.items(), key=lambda x: -x[1])[:5]]
        },
        "goal_analysis": {
            "short_term_success": round(short_term_success,1),
            "long_term_success": round(long_term_success,1),
            "avg_completion_short": round(avg_completion_short,1),
            "avg_completion_long": round(avg_completion_long,1)
        },
        "category_analysis": category_analysis,
        "weekly_comparison": None
    }
    SMART_INSIGHTS_CACHE[current_user.id] = {"signature": signature, "timestamp": time(), "payload": payload}
    return payload


@router.get("/tasks/missed")
def get_missed_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    # Get all tasks from yesterday and before that are failed or pending
    missed_tasks = db.query(Task).filter(
        Task.user_id == current_user.id,
        Task.date < today,
        Task.status.in_(["pending", "failed"])
    ).all()
    
    return {
        "count": len(missed_tasks),
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "date": t.date,
                "status": t.status
            } for t in missed_tasks
        ]
    }
