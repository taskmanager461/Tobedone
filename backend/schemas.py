from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Difficulty = Literal["easy", "medium", "hard"]
TaskStatus = Literal["pending", "completed", "failed"]
GoalStatus = Literal["active", "achieved", "failed"]
GoalPressureStatus = Literal["on_track", "at_risk", "overdue"]
GoalType = Literal["today", "tomorrow", "three_days", "one_week", "two_weeks", "one_month", "three_months", "six_months", "one_year", "one_year_plus"]
HabitFrequencyType = Literal["daily", "weekly"]
HabitTrackStatus = Literal["completed", "skipped"]


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=2, max_length=100)


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    user_id: int
    username: str
    name: str
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    name: str
    streak: int
    created_at: datetime


Priority = Literal["low", "medium", "high"]
Recurring = Literal["none", "daily", "weekly"]

class TaskCreate(BaseModel):
    user_id: Optional[int] = None
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = Field(default="general", min_length=2, max_length=50)
    difficulty: Optional[Difficulty] = "medium"
    priority: Optional[Priority] = "medium"
    recurring: Optional[Recurring] = "none"
    due_date: Optional[date] = None
    time: Optional[str] = None
    goal_id: Optional[int] = None
    date: date


class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    time: Optional[str] = None
    goal_id: Optional[int] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    goal_id: Optional[int]
    title: str
    category: str
    difficulty: Difficulty
    priority: Priority
    recurring: Recurring
    due_date: Optional[date]
    time: Optional[str]
    status: TaskStatus
    date: date
    created_at: datetime


class GoalCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    category: Optional[str] = Field(default="general", min_length=2, max_length=50)
    deadline: date
    goal_type: GoalType = "mid_term"


class GoalUpdate(BaseModel):
    status: Optional[GoalStatus] = None
    reflection_went_well: Optional[str] = None
    reflection_didnt_go_well: Optional[str] = None


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    category: str
    deadline: date
    status: GoalStatus
    pressure_status: GoalPressureStatus
    goal_type: GoalType
    reflection_went_well: Optional[str] = None
    reflection_didnt_go_well: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    linked_tasks_count: int = 0
    completed_tasks_count: int = 0
    progress_percent: float = 0.0
    days_remaining: Optional[int] = None


class GoalAnalyticsResponse(BaseModel):
    goal_completion_rate: float
    goals_achieved: int
    goals_failed: int
    average_completion_time_days: float
    insights: list[str]


class HabitCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    category: Optional[str] = Field(default="general", min_length=2, max_length=50)
    frequency_type: HabitFrequencyType = "daily"
    frequency_days: Optional[list[int]] = None
    preferred_time: Optional[str] = None


class HabitTrackRequest(BaseModel):
    status: HabitTrackStatus
    day: Optional[date] = None


class HabitResponse(BaseModel):
    id: int
    title: str
    category: str
    frequency_type: HabitFrequencyType
    frequency_days: list[int]
    preferred_time: Optional[str]
    streak: int
    best_streak: int
    consistency_score: float
    is_due_today: bool
    today_status: Optional[HabitTrackStatus]
    is_active: bool
    created_at: datetime


class BadgeResponse(BaseModel):
    id: str
    label: str
    unlocked: bool


class IdentityProfileResponse(BaseModel):
    level: int
    total_xp: int
    next_level: int
    next_level_xp: int
    xp_into_current_level: int
    xp_for_next_level: int
    level_progress_percent: float
    trust_score: float
    completed_tasks: int
    completed_goals: int
    streak: int
    badges: list[BadgeResponse]


class DailyScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date: date
    score: float
    success_rate: float


class DailyScoreRequest(BaseModel):
    user_id: Optional[int] = None
    day: Optional[date] = None


class DailyScoreComputationResponse(BaseModel):
    date: date
    score: float
    success_rate: float
    streak: int
    multiplier: float
    total_tasks: int
    goal_bonus: float = 0.0


class PushSubscriptionBase(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


class PushSubscriptionCreate(PushSubscriptionBase):
    pass


class PushSubscriptionResponse(PushSubscriptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime


class PushNotification(BaseModel):
    title: str
    body: str
    url: str = "/"
