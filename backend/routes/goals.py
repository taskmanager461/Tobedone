from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.goal import Goal
from backend.models.user import User
from backend.schemas import GoalAnalyticsResponse, GoalCreate, GoalResponse, GoalUpdate
from backend.services.auth_service import get_current_user
from backend.services.goal_service import compute_goal_task_counts, refresh_goal_status, get_days_remaining
from backend.services.identity_service import award_goal_completion_xp

router = APIRouter(tags=["goals"])


@router.get("/goals", response_model=list[GoalResponse])
def get_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goals = (
        db.query(Goal)
        .filter(Goal.user_id == current_user.id)
        .order_by(Goal.deadline.asc(), Goal.created_at.desc())
        .all()
    )
    goal_ids = [g.id for g in goals]
    counts_map = compute_goal_task_counts(db, goal_ids)
    today = date.today()

    changed = False
    response: list[GoalResponse] = []
    for goal in goals:
        counts = counts_map.get(goal.id, {"total": 0, "completed": 0})
        previous_status = goal.status
        refresh_goal_status(goal, counts["total"], counts["completed"])
        if previous_status != goal.status:
            changed = True
        progress = (counts["completed"] / counts["total"] * 100) if counts["total"] > 0 else 0.0
        response.append(
            GoalResponse(
                id=goal.id,
                user_id=goal.user_id,
                title=goal.title,
                category=goal.category,
                deadline=goal.deadline,
                status=goal.status,
                pressure_status=goal.pressure_status,
                goal_type=goal.goal_type,
                reflection_went_well=goal.reflection_went_well,
                reflection_didnt_go_well=goal.reflection_didnt_go_well,
                created_at=goal.created_at,
                completed_at=goal.completed_at,
                linked_tasks_count=counts["total"],
                completed_tasks_count=counts["completed"],
                progress_percent=round(progress, 1),
                days_remaining=get_days_remaining(goal, today),
            )
        )
    if changed:
        db.commit()
    return response


@router.post("/goals", response_model=GoalResponse)
def create_goal(
    payload: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.deadline < date.today():
        raise HTTPException(status_code=400, detail="Deadline cannot be in the past")
    
    today = date.today()
    goal_type_ranges = {
        "today": (0, 0),
        "tomorrow": (1, 1),
        "three_days": (1, 3),
        "one_week": (1, 7),
        "two_weeks": (7, 14),
        "one_month": (14, 30),
        "three_months": (30, 90),
        "six_months": (90, 180),
        "one_year": (180, 365),
        "one_year_plus": (365, 3650),
    }
    
    if payload.goal_type in goal_type_ranges:
        min_days, max_days = goal_type_ranges[payload.goal_type]
        days_until_deadline = (payload.deadline - today).days
        
        if days_until_deadline < min_days or days_until_deadline > max_days:
            type_labels = {
                "today": "Today",
                "tomorrow": "Tomorrow",
                "three_days": "1-3 days",
                "one_week": "1 week",
                "two_weeks": "1-2 weeks",
                "one_month": "1 month",
                "three_months": "3 months",
                "six_months": "6 months",
                "one_year": "1 year",
                "one_year_plus": "1 year+",
            }
            raise HTTPException(
                status_code=400, 
                detail=f"This deadline is outside the range for {type_labels[payload.goal_type]} goals"
            )

    goal = Goal(
        user_id=current_user.id,
        title=payload.title.strip(),
        category=(payload.category or "general").strip().lower(),
        deadline=payload.deadline,
        status="active",
        goal_type=payload.goal_type,
        pressure_status="on_track",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return GoalResponse(
        id=goal.id,
        user_id=goal.user_id,
        title=goal.title,
        category=goal.category,
        deadline=goal.deadline,
        status=goal.status,
        pressure_status=goal.pressure_status,
        goal_type=goal.goal_type,
        reflection_went_well=goal.reflection_went_well,
        reflection_didnt_go_well=goal.reflection_didnt_go_well,
        created_at=goal.created_at,
        completed_at=goal.completed_at,
        linked_tasks_count=0,
        completed_tasks_count=0,
        progress_percent=0.0,
        days_remaining=get_days_remaining(goal, date.today()),
    )


@router.patch("/goals/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    payload: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    previous_status = goal.status

    if payload.status is not None:
        goal.status = payload.status
        if payload.status == "achieved" and goal.completed_at is None:
            goal.completed_at = datetime.utcnow()
        elif payload.status == "failed" and goal.completed_at is None:
            goal.completed_at = datetime.utcnow()
        elif payload.status == "active":
            goal.completed_at = None
    if payload.reflection_went_well is not None:
        goal.reflection_went_well = payload.reflection_went_well
    if payload.reflection_didnt_go_well is not None:
        goal.reflection_didnt_go_well = payload.reflection_didnt_go_well

    if goal.status == "achieved" and previous_status != "achieved" and not goal.xp_awarded:
        award_goal_completion_xp(db, current_user, goal)
        goal.xp_awarded = True
    
    db.commit()
    db.refresh(goal)
    
    counts_map = compute_goal_task_counts(db, [goal.id])
    counts = counts_map.get(goal.id, {"total": 0, "completed": 0})
    progress = (counts["completed"] / counts["total"] * 100) if counts["total"] > 0 else 0.0
    
    return GoalResponse(
        id=goal.id,
        user_id=goal.user_id,
        title=goal.title,
        category=goal.category,
        deadline=goal.deadline,
        status=goal.status,
        pressure_status=goal.pressure_status,
        goal_type=goal.goal_type,
        reflection_went_well=goal.reflection_went_well,
        reflection_didnt_go_well=goal.reflection_didnt_go_well,
        created_at=goal.created_at,
        completed_at=goal.completed_at,
        linked_tasks_count=counts["total"],
        completed_tasks_count=counts["completed"],
        progress_percent=round(progress, 1),
        days_remaining=get_days_remaining(goal, date.today()),
    )


@router.delete("/goals/{goal_id}")
def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    db.delete(goal)
    db.commit()
    return {"message": "Goal deleted successfully"}


@router.get("/goals/analytics", response_model=GoalAnalyticsResponse)
def goals_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    goal_ids = [g.id for g in goals]
    counts_map = compute_goal_task_counts(db, goal_ids)

    achieved = 0
    failed = 0
    completion_days: list[float] = []
    short_term_days: list[float] = []
    long_term_days: list[float] = []

    for goal in goals:
        counts = counts_map.get(goal.id, {"total": 0, "completed": 0})
        refresh_goal_status(goal, counts["total"], counts["completed"])
        if goal.status == "achieved":
            achieved += 1
            if goal.completed_at:
                days = (goal.completed_at.date() - goal.created_at.date()).days
                completion_days.append(max(0, float(days)))
                target_span = (goal.deadline - goal.created_at.date()).days
                if target_span <= 14:
                    short_term_days.append(max(0, float(days)))
                if target_span >= 30:
                    long_term_days.append(max(0, float(days)))
        elif goal.status == "failed":
            failed += 1

    db.commit()

    total_goals = len(goals)
    completion_rate = (achieved / total_goals * 100) if total_goals > 0 else 0.0
    avg_completion_time = sum(completion_days) / len(completion_days) if completion_days else 0.0

    insights: list[str] = []
    if short_term_days and long_term_days and (sum(short_term_days) / len(short_term_days)) < (sum(long_term_days) / len(long_term_days)):
        insights.append("You complete short-term goals faster")
    if failed > achieved and total_goals >= 3:
        insights.append("You struggle with long-term goals")
    if not insights and total_goals > 0:
        insights.append("Your goal consistency is improving")

    return GoalAnalyticsResponse(
        goal_completion_rate=round(completion_rate, 1),
        goals_achieved=achieved,
        goals_failed=failed,
        average_completion_time_days=round(avg_completion_time, 1),
        insights=insights,
    )
