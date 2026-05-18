from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.goal import Goal
from backend.models.task import Task
from backend.models.user import User
from backend.schemas import TaskCreate, TaskResponse, TaskUpdate
from backend.services.auth_service import get_current_user
from backend.services.goal_service import refresh_goal_status_by_id
from backend.services.identity_service import award_task_completion_xp

router = APIRouter(tags=["tasks"])


@router.get("/tasks", response_model=list[TaskResponse])
def get_tasks(
    user_id: int | None = Query(default=None),
    day: date = Query(...),
    category: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_user_id = user_id or current_user.id
    if target_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    query = db.query(Task).filter(Task.user_id == target_user_id, Task.date == day)
    
    if category:
        query = query.filter(Task.category == category.lower())
    if priority:
        query = query.filter(Task.priority == priority)
    if status:
        query = query.filter(Task.status == status)

    tasks = query.order_by(Task.created_at.asc()).all()
    return tasks


@router.get("/tasks/range", response_model=list[TaskResponse])
def get_tasks_range(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks = db.query(Task).filter(
        Task.user_id == current_user.id,
        Task.date >= start_date,
        Task.date <= end_date
    ).all()
    return tasks


@router.post("/tasks", response_model=TaskResponse)
def create_task(payload: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    target_user_id = payload.user_id or current_user.id
    if target_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if payload.goal_id is not None:
        goal = db.query(Goal).filter(Goal.id == payload.goal_id, Goal.user_id == current_user.id).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

    task = Task(
        user_id=target_user_id,
        goal_id=payload.goal_id,
        title=payload.title,
        description=payload.description,
        category=(payload.category or "general").lower(),
        difficulty=payload.difficulty or "medium",
        priority=payload.priority or "medium",
        recurring=payload.recurring or "none",
        due_date=payload.due_date,
        time=payload.time,
        status="pending",
        date=payload.date,
    )
    db.add(task)
    db.commit()
    if task.goal_id:
        refresh_goal_status_by_id(db, task.goal_id)
        db.commit()
    db.refresh(task)

    return task


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    previous_goal_id = task.goal_id
    previous_status = task.status

    if payload.status:
        if payload.status not in {"completed", "failed", "pending"}:
            raise HTTPException(status_code=400, detail="Invalid task status")
        task.status = payload.status
    
    if payload.priority:
        if payload.priority not in {"low", "medium", "high"}:
            raise HTTPException(status_code=400, detail="Invalid priority")
        task.priority = payload.priority

    if payload.goal_id is not None:
        if payload.goal_id <= 0:
            task.goal_id = None
        else:
            goal = db.query(Goal).filter(Goal.id == payload.goal_id, Goal.user_id == current_user.id).first()
            if not goal:
                raise HTTPException(status_code=404, detail="Goal not found")
            task.goal_id = payload.goal_id

    if task.status == "completed" and previous_status != "completed" and not task.xp_awarded:
        award_task_completion_xp(db, current_user, task)
        task.xp_awarded = True

    db.commit()

    if previous_goal_id:
        refresh_goal_status_by_id(db, previous_goal_id)
    if task.goal_id:
        refresh_goal_status_by_id(db, task.goal_id)
    if previous_goal_id or task.goal_id:
        db.commit()

    db.refresh(task)

    return task
