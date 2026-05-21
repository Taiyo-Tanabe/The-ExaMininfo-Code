import io, base64
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from PIL import Image
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas, models
from ..auth import get_current_user, require_roles
from ..functions.functions_users import (
    list_users, register_user, login_user, update_profile, change_password,
    update_user_role, get_user_public, follow_user, unfollow_user,
    get_follow_status, get_followers_list, get_following_list,
    delete_user, delete_self, list_blocked_emails, unblock_email,
)
from ..functions.functions_reviews import list_user_reviews

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=schemas.Page[schemas.UserOut])
def list_users_route(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _ = Depends(require_roles(["admin"])),
):
    return list_users(db, skip, limit)


@router.post("/register", response_model=schemas.UserOut)
def register_route(data: schemas.UserCreate, db: Session = Depends(get_db)):
    return register_user(db, data)


@router.post("/login", response_model=schemas.Token)
def login_route(data: schemas.UserLogin, db: Session = Depends(get_db)):
    return login_user(db, data)


@router.get("/me", response_model=schemas.UserOut)
def get_me_route(current_user=Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=schemas.UserOut)
def update_profile_route(
    data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_profile(db, data, current_user)


@router.post("/me/change-password")
def change_password_route(
    data: schemas.ChangePassword,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return change_password(db, data, current_user)


@router.get("/search", response_model=schemas.Page[schemas.UserPublicOut])
def search_users_route(
    q: str = "",
    limit: int = 8,
    db: Session = Depends(get_db),
):
    query = db.query(models.User)
    if q:
        query = query.filter(models.User.name.ilike(f"%{q}%"))
    total = query.count()
    users = query.limit(limit).all()
    return {
        "total": total, "skip": 0, "limit": limit,
        "items": [
            {"id": u.id, "name": u.name, "bio": u.bio, "avatar_url": u.avatar_url,
             "follower_count": 0, "following_count": 0}
            for u in users
        ],
    }


@router.patch("/{user_id}/role", response_model=schemas.UserOut)
def update_user_role_route(
    user_id: int,
    data: schemas.RoleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["admin"])),
):
    return update_user_role(db, user_id, data, current_user)


@router.get("/{user_id}/profile", response_model=schemas.UserPublicOut)
def get_user_public_route(user_id: int, db: Session = Depends(get_db)):
    return get_user_public(db, user_id)


@router.post("/{user_id}/follow")
def follow_user_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return follow_user(db, user_id, current_user)


@router.delete("/{user_id}/follow")
def unfollow_user_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return unfollow_user(db, user_id, current_user)


@router.get("/{user_id}/follow-status", response_model=schemas.FollowStatus)
def follow_status_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_follow_status(db, user_id, current_user)


@router.post("/me/avatar")
def upload_avatar_route(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="jpeg/png/webp/gifのみ対応しています")

    data = file.file.read()
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((256, 256), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    data_url = f"data:image/jpeg;base64,{b64}"

    current_user.avatar_url = data_url
    db.commit()
    db.refresh(current_user)
    return {"avatar_url": data_url}


@router.get("/{user_id}/followers")
def get_followers_route(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return get_followers_list(db, user_id, skip, limit)


@router.get("/{user_id}/following")
def get_following_route(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return get_following_list(db, user_id, skip, limit)


@router.get("/{user_id}/reviews", response_model=schemas.Page[schemas.ReviewOut])
def get_user_reviews_route(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return list_user_reviews(db, user_id, skip, limit)


@router.get("/blocked-emails")
def list_blocked_emails_route(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _ = Depends(require_roles(["admin"])),
):
    return list_blocked_emails(db, skip, limit)


@router.delete("/blocked-emails/{email_id}")
def unblock_email_route(
    email_id: int,
    db: Session = Depends(get_db),
    _ = Depends(require_roles(["admin"])),
):
    return unblock_email(db, email_id)


@router.delete("/me")
def delete_self_route(
    data: schemas.DeleteSelf,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return delete_self(db, data.password, current_user)


@router.delete("/{user_id}")
def delete_user_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["admin"])),
):
    return delete_user(db, user_id, current_user)
