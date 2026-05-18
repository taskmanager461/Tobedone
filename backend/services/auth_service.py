import re

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from config.settings import get_settings

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def _slugify_username(value: str) -> str:
    normalized = (value or "").strip().lower()
    normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        normalized = "user"
    if len(normalized) < 3:
        normalized = (normalized + "_000")[:3]
    return normalized[:50]


def _reserve_unique_username(db: Session, preferred: str, current_user_id: int | None = None) -> str:
    base = _slugify_username(preferred)
    candidate = base
    for i in range(0, 50):
        existing = db.query(User).filter(User.username == candidate).first()
        if not existing or (current_user_id is not None and existing.id == current_user_id):
            return candidate
        suffix = str(i + 1)
        cut = max(3, 50 - (len(suffix) + 1))
        candidate = f"{base[:cut]}_{suffix}"
    return f"{base[:42]}_{base[-8:]}"


def _get_supabase_user(access_token: str) -> dict:
    url = f"{settings.supabase_project_url}/auth/v1/user"
    headers = {"Authorization": f"Bearer {access_token}", "apikey": settings.supabase_anon_key}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return response.json()


def _get_or_create_local_user(db: Session, sb_user: dict) -> User:
    sb_id = (sb_user.get("id") or "").strip()
    if not sb_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    email = (sb_user.get("email") or "").strip().lower()
    meta = sb_user.get("user_metadata") or {}
    raw_username = (
        (meta.get("username") or "").strip()
        or (meta.get("preferred_username") or "").strip()
        or (email.split("@")[0].strip() if "@" in email else "")
        or f"user_{sb_id[:8]}"
    )
    raw_name = (
        (meta.get("name") or "").strip()
        or (meta.get("full_name") or "").strip()
        or (meta.get("display_name") or "").strip()
    )

    user = db.query(User).filter(User.supabase_id == sb_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        username = _reserve_unique_username(db, raw_username)
        safe_email = email or f"{sb_id}@supabase.local"
        user = User(
            supabase_id=sb_id,
            username=username,
            email=safe_email,
            password="SUPABASE_AUTH",
            name=raw_name or username,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    changed = False
    if not user.supabase_id:
        user.supabase_id = sb_id
        changed = True

    if email and user.email != email:
        email_taken = db.query(User).filter(User.email == email, User.id != user.id).first()
        if not email_taken:
            user.email = email
            changed = True

    desired_username = _reserve_unique_username(db, raw_username, current_user_id=user.id)
    if desired_username and user.username != desired_username:
        user.username = desired_username
        changed = True

    desired_name = (raw_name or "").strip()
    if desired_name and user.name != desired_name:
        user.name = desired_name
        changed = True

    if changed:
        db.commit()
        db.refresh(user)
    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sb_user = _get_supabase_user(token)
    return _get_or_create_local_user(db, sb_user)
