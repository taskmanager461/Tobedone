from fastapi import APIRouter, Depends, HTTPException

from backend.models.user import User
from backend.schemas import AuthResponse, LoginRequest, SignupRequest
from backend.services.auth_service import get_current_user

router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignupRequest):
    raise HTTPException(status_code=410, detail="Use Supabase Auth for signup")


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    raise HTTPException(status_code=410, detail="Use Supabase Auth for login")


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "name": current_user.name,
    }
