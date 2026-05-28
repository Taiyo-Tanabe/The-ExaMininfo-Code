from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import hash_password, verify_password, create_access_token


def list_users(db: Session, skip: int = 0, limit: int = 100):
    total = db.query(models.User).count()
    items = db.query(models.User).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


def register_user(db: Session, data: schemas.UserCreate):
    if db.query(models.BlockedEmail).filter(models.BlockedEmail.email == data.email).first():
        raise HTTPException(status_code=400, detail="このメールアドレスは使用できません")
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 最初のユーザーはadminとして自動承認
    is_first = db.query(models.User).count() == 0
    user = models.User(
        name=data.name,
        email=data.email,
        password=hash_password(data.password),
        role="admin" if is_first else "user",
        is_approved=is_first,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, data: schemas.UserLogin):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email")
    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


def update_profile(db: Session, data: schemas.UserUpdate, current_user: models.User):
    if data.name is not None:
        current_user.name = data.name
    if data.email is not None:
        if db.query(models.User).filter(models.User.email == data.email, models.User.id != current_user.id).first():
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = data.email
    if data.bio is not None:
        current_user.bio = data.bio
    if data.avatar_position_x is not None:
        current_user.avatar_position_x = data.avatar_position_x
    if data.avatar_position_y is not None:
        current_user.avatar_position_y = data.avatar_position_y
    db.commit()
    db.refresh(current_user)
    return current_user


def get_user_public(db: Session, user_id: int) -> dict:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    follower_count = db.query(models.Follow).filter(models.Follow.following_id == user_id).count()
    following_count = db.query(models.Follow).filter(models.Follow.follower_id == user_id).count()
    return {
        "id": user.id,
        "name": user.name,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "avatar_position_x": user.avatar_position_x,
        "avatar_position_y": user.avatar_position_y,
        "follower_count": follower_count,
        "following_count": following_count,
    }


def follow_user(db: Session, target_id: int, current_user: models.User):
    if target_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    if not db.query(models.User).filter(models.User.id == target_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.query(models.Follow).filter(
        models.Follow.follower_id == current_user.id,
        models.Follow.following_id == target_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already following")
    follow = models.Follow(follower_id=current_user.id, following_id=target_id)
    db.add(follow)
    db.commit()
    return {"message": "followed"}


def unfollow_user(db: Session, target_id: int, current_user: models.User):
    follow = db.query(models.Follow).filter(
        models.Follow.follower_id == current_user.id,
        models.Follow.following_id == target_id,
    ).first()
    if not follow:
        raise HTTPException(status_code=404, detail="Not following")
    db.delete(follow)
    db.commit()
    return {"message": "unfollowed"}


def get_follow_status(db: Session, target_id: int, current_user: models.User) -> dict:
    exists = db.query(models.Follow).filter(
        models.Follow.follower_id == current_user.id,
        models.Follow.following_id == target_id,
    ).first()
    return {"is_following": bool(exists)}


def get_followers_list(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> dict:
    if not db.query(models.User).filter(models.User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    follows = (
        db.query(models.Follow)
        .filter(models.Follow.following_id == user_id)
        .offset(skip).limit(limit).all()
    )
    total = db.query(models.Follow).filter(models.Follow.following_id == user_id).count()
    items = []
    for f in follows:
        u = db.query(models.User).filter(models.User.id == f.follower_id).first()
        if u:
            items.append({"id": u.id, "name": u.name, "bio": u.bio, "avatar_url": u.avatar_url})
    return {"total": total, "skip": skip, "limit": limit, "items": items}


def get_following_list(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> dict:
    if not db.query(models.User).filter(models.User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    follows = (
        db.query(models.Follow)
        .filter(models.Follow.follower_id == user_id)
        .offset(skip).limit(limit).all()
    )
    total = db.query(models.Follow).filter(models.Follow.follower_id == user_id).count()
    items = []
    for f in follows:
        u = db.query(models.User).filter(models.User.id == f.following_id).first()
        if u:
            items.append({"id": u.id, "name": u.name, "bio": u.bio, "avatar_url": u.avatar_url})
    return {"total": total, "skip": skip, "limit": limit, "items": items}


def change_password(db: Session, data: schemas.ChangePassword, current_user: models.User):
    if not verify_password(data.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password updated"}


def update_user_role(db: Session, user_id: int, data: schemas.RoleUpdate, current_user):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if data.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    user.role = data.role
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int, current_user: models.User):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself via this endpoint")
    email = user.email
    db.delete(user)
    if not db.query(models.BlockedEmail).filter(models.BlockedEmail.email == email).first():
        db.add(models.BlockedEmail(email=email))
    db.commit()
    return {"message": f"user {user_id} deleted and email blocked"}


def list_blocked_emails(db: Session, skip: int = 0, limit: int = 100):
    total = db.query(models.BlockedEmail).count()
    items = (
        db.query(models.BlockedEmail)
        .order_by(models.BlockedEmail.blocked_at.desc())
        .offset(skip).limit(limit).all()
    )
    return {"total": total, "skip": skip, "limit": limit, "items": items}


def unblock_email(db: Session, email_id: int):
    entry = db.query(models.BlockedEmail).filter(models.BlockedEmail.id == email_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(entry)
    db.commit()
    return {"message": "unblocked"}


def delete_self(db: Session, password: str, current_user: models.User):
    from ..auth import verify_password
    if not verify_password(password, current_user.password):
        raise HTTPException(status_code=400, detail="パスワードが正しくありません")
    db.delete(current_user)
    db.commit()
    return {"message": "account deleted"}


def list_pending_users(db: Session, skip: int = 0, limit: int = 100) -> dict:
    query = db.query(models.User).filter(models.User.is_approved == False)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


def approve_user(db: Session, user_id: int) -> models.User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_approved = True
    db.commit()
    db.refresh(user)
    return user
