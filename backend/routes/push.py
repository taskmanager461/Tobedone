import os
import json
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pywebpush import webpush, WebPushException

from backend.database import get_db
from backend.models.push_subscription import PushSubscription
from backend.models.user import User
from backend.models.task import Task
from backend.models.habit import Habit
from backend.models.habit_log import HabitLog
from backend.schemas import PushSubscriptionCreate, PushSubscriptionResponse, PushNotification
from backend.services.auth_service import get_current_user
from backend.services.habit_service import is_habit_due_on

router = APIRouter(tags=["push"])

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS = {"sub": "mailto:admin@tobedone.app"}


def send_push_notification(subscription: PushSubscription, notification: PushNotification) -> bool:
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps(
                {
                    "title": notification.title,
                    "body": notification.body,
                    "url": notification.url,
                }
            ),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS,
        )
        return True
    except WebPushException as e:
        print(f"Push notification failed: {e}")
        return False


@router.post("/push/subscribe", response_model=PushSubscriptionResponse)
def subscribe_push(
    payload: PushSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(PushSubscription).filter(
        PushSubscription.user_id == current_user.id,
        PushSubscription.endpoint == payload.endpoint,
    ).first()
    if existing:
        existing.p256dh = payload.p256dh
        existing.auth = payload.auth
        db.commit()
        db.refresh(existing)
        return existing

    subscription = PushSubscription(
        user_id=current_user.id,
        endpoint=payload.endpoint,
        p256dh=payload.p256dh,
        auth=payload.auth,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.delete("/push/unsubscribe")
def unsubscribe_push(
    endpoint: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subscription = db.query(PushSubscription).filter(
        PushSubscription.user_id == current_user.id,
        PushSubscription.endpoint == endpoint,
    ).first()
    if subscription:
        db.delete(subscription)
        db.commit()
    return {"success": True}


@router.get("/push/vapid-key")
def get_vapid_key():
    return {"public_key": VAPID_PUBLIC_KEY}


@router.post("/push/send")
def send_test_push(
    notification: PushNotification,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subscriptions = db.query(PushSubscription).filter(PushSubscription.user_id == current_user.id).all()
    success_count = 0
    for sub in subscriptions:
        if send_push_notification(sub, notification):
            success_count += 1
    return {"sent": success_count, "total": len(subscriptions)}


def run_scheduled_jobs(db: Session):
    today = date.today()
    now = datetime.now()

    users = db.query(User).all()
    for user in users:
        subscriptions = db.query(PushSubscription).filter(PushSubscription.user_id == user.id).all()
        if not subscriptions:
            continue

        # A. Task Reminders (15 mins before time)
        today_tasks = db.query(Task).filter(
            Task.user_id == user.id, Task.date == today, Task.status == "pending", Task.time.isnot(None)
        ).all()
        for task in today_tasks:
            try:
                task_time = datetime.strptime(task.time, "%H:%M").time()
                task_datetime = datetime.combine(today, task_time)
                diff_minutes = (task_datetime - now).total_seconds() / 60
                if 0 < diff_minutes <= 15:
                    notif = PushNotification(
                        title=f"Reminder: {task.title}",
                        body=f"Your task is due in {int(diff_minutes)} minutes!",
                        url="/tasks",
                    )
                    for sub in subscriptions:
                        send_push_notification(sub, notif)
            except Exception:
                pass

        # Habit reminders
        today_habits = db.query(Habit).filter(Habit.user_id == user.id, Habit.is_active.is_(True)).all()
        for habit in today_habits:
            if not is_habit_due_on(habit, today):
                continue
            today_log = db.query(HabitLog).filter(
                HabitLog.habit_id == habit.id, HabitLog.user_id == user.id, HabitLog.date == today
            ).first()
            if today_log and today_log.status == "completed":
                continue
            if not habit.preferred_time:
                continue
            try:
                habit_time = datetime.strptime(habit.preferred_time, "%H:%M").time()
                habit_datetime = datetime.combine(today, habit_time)
                diff_minutes = (habit_datetime - now).total_seconds() / 60
                if 0 < diff_minutes <= 15:
                    notif = PushNotification(
                        title=f"Habit Reminder: {habit.title}",
                        body=f"Stay consistent. '{habit.title}' is due in {int(diff_minutes)} minutes.",
                        url="/tasks",
                    )
                    for sub in subscriptions:
                        send_push_notification(sub, notif)
            except Exception:
                pass

        # B. Missed Task Alert
        missed_tasks = db.query(Task).filter(
            Task.user_id == user.id, Task.date < today, Task.status.in_(["pending", "failed"])
        ).count()
        if missed_tasks > 0 and now.hour == 9:
            notif = PushNotification(
                title="Missed Tasks Alert",
                body=f"You have {missed_tasks} missed task{'' if missed_tasks == 1 else 's'}!",
                url="/tasks",
            )
            for sub in subscriptions:
                send_push_notification(sub, notif)

        # C. Streak Warning
        completed_today = db.query(Task).filter(
            Task.user_id == user.id, Task.date == today, Task.status == "completed"
        ).count()
        if user.streak > 0 and completed_today == 0 and now.hour == 18:
            notif = PushNotification(
                title="Streak at Risk!",
                body="Complete at least one task today to keep your streak!",
                url="/tasks",
            )
            for sub in subscriptions:
                send_push_notification(sub, notif)

        # D. Daily Nudge
        today_tasks_total = db.query(Task).filter(Task.user_id == user.id, Task.date == today).count()
        if today_tasks_total > 0 and completed_today == 0 and now.hour == 14:
            notif = PushNotification(
                title="Don't Forget Your Tasks!",
                body="You have tasks pending today. Let's get started!",
                url="/tasks",
            )
            for sub in subscriptions:
                send_push_notification(sub, notif)

        # Habit nudge
        if now.hour == 20:
            due_habits = [h for h in today_habits if is_habit_due_on(h, today)]
            if due_habits:
                completed_habits = db.query(HabitLog).filter(
                    HabitLog.user_id == user.id,
                    HabitLog.date == today,
                    HabitLog.status == "completed",
                    HabitLog.habit_id.in_([h.id for h in due_habits]),
                ).count()
                if completed_habits < len(due_habits):
                    pending_count = len(due_habits) - completed_habits
                    notif = PushNotification(
                        title="Gentle Habit Nudge",
                        body=f"You still have {pending_count} habit{'' if pending_count == 1 else 's'} pending today.",
                        url="/tasks",
                    )
                    for sub in subscriptions:
                        send_push_notification(sub, notif)

        # E. Weekly Summary (Sunday 10 AM)
        if today.weekday() == 6 and now.hour == 10:
            week_start = today - date.timedelta(days=6)
            week_tasks = db.query(Task).filter(
                Task.user_id == user.id, Task.date >= week_start, Task.date <= today
            ).all()
            total_week = len(week_tasks)
            completed_week = sum(1 for t in week_tasks if t.status == "completed")
            notif = PushNotification(
                title="Weekly Performance Ready!",
                body=f"You completed {completed_week}/{total_week} tasks this week!",
                url="/weekly",
            )
            for sub in subscriptions:
                send_push_notification(sub, notif)
