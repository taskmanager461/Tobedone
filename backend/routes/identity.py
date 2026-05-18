from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.schemas import IdentityProfileResponse
from backend.services.auth_service import get_current_user
from backend.services.identity_service import get_identity_profile

router = APIRouter(tags=["identity"])


@router.get("/identity/profile", response_model=IdentityProfileResponse)
def identity_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_identity_profile(db, current_user)
