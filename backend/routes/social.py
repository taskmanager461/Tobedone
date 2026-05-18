from datetime import datetime
from sqlalchemy import or_, and_, func, desc
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

from backend.database import get_db
from backend.models.user import User
from backend.models.social import Friendship, FriendshipStatus, UserSocialProfile
from backend.models.goal import Goal
from backend.services.auth_service import get_current_user


router = APIRouter(tags=["social"])


# --- Helper to get or create social profile ---
def get_or_create_social_profile(db: Session, user_id: int) -> UserSocialProfile:
    profile = db.query(UserSocialProfile).filter(UserSocialProfile.user_id == user_id).first()
    if not profile:
        profile = UserSocialProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


# --- Social Profile ---
@router.get("/social/profile")
def get_my_social_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = get_or_create_social_profile(db, current_user.id)
    goals_achieved = db.query(Goal).filter(
        Goal.user_id == current_user.id,
        Goal.status == "achieved"
    ).count()
    
    return {
        "username": current_user.username,
        "name": current_user.name,
        "level": current_user.level,
        "streak": current_user.streak,
        "total_xp": current_user.total_xp,
        "trust_score": current_user.trust_score,
        "goals_achieved": goals_achieved,
        "public_profile": profile.public_profile,
        "show_level": profile.show_level,
        "show_streak": profile.show_streak,
        "show_xp": profile.show_xp,
        "bio": profile.bio,
        "created_at": current_user.created_at.isoformat()
    }


@router.get("/social/profile/{username}")
def get_public_profile(
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = get_or_create_social_profile(db, user.id)
    
    if not profile.public_profile and user.id != current_user.id:
        # Check if they are friends
        friendship = db.query(Friendship).filter(
            or_(
                and_(Friendship.user_id == current_user.id, Friendship.friend_id == user.id),
                and_(Friendship.user_id == user.id, Friendship.friend_id == current_user.id)
            ),
            Friendship.status == FriendshipStatus.ACCEPTED
        ).first()
        
        if not friendship:
            raise HTTPException(status_code=403, detail="This profile is private")
    
    goals_achieved = db.query(Goal).filter(
        Goal.user_id == user.id,
        Goal.status == "achieved"
    ).count()
    
    return {
        "username": user.username,
        "name": user.name,
        "level": profile.show_level and user.level or None,
        "streak": profile.show_streak and user.streak or None,
        "total_xp": profile.show_xp and user.total_xp or None,
        "trust_score": user.trust_score,
        "goals_achieved": goals_achieved,
        "bio": profile.bio,
        "created_at": user.created_at.isoformat()
    }


@router.put("/social/profile")
def update_social_profile(
    public_profile: bool | None = None,
    show_level: bool | None = None,
    show_streak: bool | None = None,
    show_xp: bool | None = None,
    bio: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = get_or_create_social_profile(db, current_user.id)
    
    if public_profile is not None:
        profile.public_profile = public_profile
    if show_level is not None:
        profile.show_level = show_level
    if show_streak is not None:
        profile.show_streak = show_streak
    if show_xp is not None:
        profile.show_xp = show_xp
    if bio is not None:
        profile.bio = bio
    
    db.commit()
    db.refresh(profile)
    
    return {"message": "Profile updated successfully"}


# --- Friendship System ---
@router.post("/social/friends/request/{username}")
def send_friend_request(
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    friend = db.query(User).filter(User.username == username).first()
    if not friend:
        raise HTTPException(status_code=404, detail="User not found")
    if friend.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself as friend")
    
    # Check if friendship already exists
    existing = db.query(Friendship).filter(
        or_(
            and_(Friendship.user_id == current_user.id, Friendship.friend_id == friend.id),
            and_(Friendship.user_id == friend.id, Friendship.friend_id == current_user.id)
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Friendship already exists")
    
    friendship = Friendship(user_id=current_user.id, friend_id=friend.id)
    db.add(friendship)
    db.commit()
    
    return {"message": "Friend request sent"}


@router.get("/social/friends/requests")
def get_friend_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    requests = db.query(Friendship).filter(
        Friendship.friend_id == current_user.id,
        Friendship.status == FriendshipStatus.PENDING
    ).all()
    
    results = []
    for req in requests:
        user = db.query(User).filter(User.id == req.user_id).first()
        if user:
            results.append({
                "id": req.id,
                "username": user.username,
                "name": user.name,
                "sent_at": req.created_at.isoformat()
            })
    return results


@router.post("/social/friends/requests/{request_id}/accept")
def accept_friend_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    friendship = db.query(Friendship).filter(
        Friendship.id == request_id,
        Friendship.friend_id == current_user.id,
        Friendship.status == FriendshipStatus.PENDING
    ).first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Request not found")
    
    friendship.status = FriendshipStatus.ACCEPTED
    db.commit()
    
    return {"message": "Friend request accepted"}


@router.post("/social/friends/requests/{request_id}/reject")
def reject_friend_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    friendship = db.query(Friendship).filter(
        Friendship.id == request_id,
        Friendship.friend_id == current_user.id,
        Friendship.status == FriendshipStatus.PENDING
    ).first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Request not found")
    
    db.delete(friendship)
    db.commit()
    
    return {"message": "Friend request rejected"}


@router.get("/social/friends")
def get_friends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    friendships = db.query(Friendship).filter(
        or_(
            and_(Friendship.user_id == current_user.id, Friendship.status == FriendshipStatus.ACCEPTED),
            and_(Friendship.friend_id == current_user.id, Friendship.status == FriendshipStatus.ACCEPTED)
        )
    ).all()
    
    friends = []
    for f in friendships:
        friend_id = f.friend_id if f.user_id == current_user.id else f.user_id
        friend = db.query(User).filter(User.id == friend_id).first()
        if friend:
            goals_achieved = db.query(Goal).filter(
                Goal.user_id == friend.id,
                Goal.status == "achieved"
            ).count()
            friends.append({
                "username": friend.username,
                "name": friend.name,
                "level": friend.level,
                "streak": friend.streak,
                "total_xp": friend.total_xp,
                "goals_achieved": goals_achieved
            })
    return friends


# --- Leaderboard ---
@router.get("/social/leaderboard")
def get_leaderboard(
    type: str = "global",  # "global" or "friends"
    metric: str = "xp",  # "xp", "streak", "goals"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    
    if type == "friends":
        friend_ids = [current_user.id]
        friendships = db.query(Friendship).filter(
            or_(
                and_(Friendship.user_id == current_user.id, Friendship.status == FriendshipStatus.ACCEPTED),
                and_(Friendship.friend_id == current_user.id, Friendship.status == FriendshipStatus.ACCEPTED)
            )
        ).all()
        for f in friendships:
            friend_id = f.friend_id if f.user_id == current_user.id else f.user_id
            friend_ids.append(friend_id)
        query = query.filter(User.id.in_(friend_ids))
    
    if metric == "xp":
        query = query.order_by(desc(User.total_xp))
    elif metric == "streak":
        query = query.order_by(desc(User.streak))
    elif metric == "goals":
        query = query.join(Goal, Goal.user_id == User.id)\
                     .filter(Goal.status == "achieved")\
                     .group_by(User.id)\
                     .order_by(desc(func.count(Goal.id)))
    else:
        query = query.order_by(desc(User.total_xp))
    
    users = query.limit(20).all()
    leaderboard = []
    
    for rank, user in enumerate(users, 1):
        goals_achieved = db.query(Goal).filter(
            Goal.user_id == user.id,
            Goal.status == "achieved"
        ).count()
        leaderboard.append({
            "rank": rank,
            "username": user.username,
            "name": user.name,
            "level": user.level,
            "streak": user.streak,
            "total_xp": user.total_xp,
            "goals_achieved": goals_achieved
        })
    
    return leaderboard
