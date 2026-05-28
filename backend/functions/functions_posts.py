from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas

_POST_SORT = {
    "created_at": models.Post.created_at,
}

_REPOST_SORT = {
    "created_at": models.Repost.created_at,
}


def _reaction_counts(db: Session, target_type: str, target_id: int) -> dict:
    rows = db.query(models.Reaction).filter(
        models.Reaction.target_type == target_type,
        models.Reaction.target_id == target_id,
    ).all()
    return {
        "like_count":    sum(1 for r in rows if r.reaction == "like"),
        "dislike_count": sum(1 for r in rows if r.reaction == "dislike"),
    }


def _fmt_post(db: Session, post: models.Post) -> dict:
    counts = _reaction_counts(db, "post", post.id)
    reply_count = db.query(models.Post).filter(models.Post.reply_to_id == post.id).count()
    user = db.query(models.User).filter(models.User.id == post.user_id).first()
    school = db.query(models.School).filter(models.School.id == post.school_id).first()
    return {
        "id":              post.id,
        "user_id":                post.user_id,
        "user_name":              user.name if user else None,
        "user_avatar_url":        user.avatar_url if user else None,
        "user_avatar_position_x": user.avatar_position_x if user else 50,
        "user_avatar_position_y": user.avatar_position_y if user else 50,
        "school_id":              post.school_id,
        "school_name":     school.name if school else None,
        "incident_id":     post.incident_id,
        "review_id":       post.review_id,
        "content":         post.content,
        "course_name":     post.course_name,
        "reply_to_id":     post.reply_to_id,
        "created_at":      post.created_at,
        "reply_count":     reply_count,
        **counts,
    }


def _fmt_repost(db: Session, repost: models.Repost) -> dict:
    counts = _reaction_counts(db, "repost", repost.id)
    user = db.query(models.User).filter(models.User.id == repost.user_id).first()
    original = db.query(models.Post).filter(models.Post.id == repost.post_id).first()
    return {
        "id":             repost.id,
        "user_id":                repost.user_id,
        "user_name":              user.name if user else None,
        "user_avatar_url":        user.avatar_url if user else None,
        "user_avatar_position_x": user.avatar_position_x if user else 50,
        "user_avatar_position_y": user.avatar_position_y if user else 50,
        "post_id":                repost.post_id,
        "comment":        repost.comment,
        "created_at":     repost.created_at,
        "original_post":  _fmt_post(db, original) if original else None,
        **counts,
    }


# ---- Post ----

def list_posts(
    db: Session,
    school_id: int = None,
    q: str = None,
    school_name: str = None,
    user_id: int = None,
    incident_id: int = None,
    review_id: int = None,
    reply_to_id: int = None,
    top_level_only: bool = False,
    replies_only: bool = False,
    sort_by: str = "created_at",
    order: str = "desc",
    skip: int = 0,
    limit: int = 20,
):
    query = db.query(models.Post)
    if user_id:
        query = query.filter(models.Post.user_id == user_id)
    if school_id:
        query = query.filter(models.Post.school_id == school_id)
    if incident_id:
        query = query.filter(models.Post.incident_id == incident_id)
    if review_id:
        query = query.filter(models.Post.review_id == review_id)
    if school_name:
        query = query.join(models.School, models.Post.school_id == models.School.id).filter(
            models.School.name.ilike(f"%{school_name}%")
        )
    if q:
        query = query.filter(models.Post.content.ilike(f"%{q}%"))
    if reply_to_id is not None:
        query = query.filter(models.Post.reply_to_id == reply_to_id)
    elif top_level_only:
        query = query.filter(models.Post.reply_to_id == None)
    elif replies_only:
        query = query.filter(models.Post.reply_to_id != None)

    total = query.count()
    col = _POST_SORT.get(sort_by, models.Post.created_at)
    posts = (
        query
        .order_by(col.desc() if order == "desc" else col.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"total": total, "skip": skip, "limit": limit, "items": [_fmt_post(db, p) for p in posts]}


def update_post(db: Session, post_id: int, data: "schemas.PostUpdate", current_user: models.User):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    if data.content is not None:
        post.content = data.content
    if data.course_name is not None:
        post.course_name = data.course_name
    db.commit()
    db.refresh(post)
    return _fmt_post(db, post)


def get_post(db: Session, post_id: int):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return _fmt_post(db, post)


def create_post(db: Session, data: schemas.PostCreate, current_user: models.User):
    if not db.query(models.School).filter(models.School.id == data.school_id).first():
        raise HTTPException(status_code=404, detail="School not found")
    if data.reply_to_id is not None:
        if not db.query(models.Post).filter(models.Post.id == data.reply_to_id).first():
            raise HTTPException(status_code=404, detail="Original post not found")
    if data.incident_id is not None:
        if not db.query(models.Incident).filter(models.Incident.id == data.incident_id).first():
            raise HTTPException(status_code=404, detail="Incident not found")
    post = models.Post(
        user_id=current_user.id, school_id=data.school_id,
        content=data.content, course_name=data.course_name,
        reply_to_id=data.reply_to_id, incident_id=data.incident_id,
        review_id=data.review_id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _fmt_post(db, post)


def delete_post(db: Session, post_id: int, current_user: models.User):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete direct replies and their associated reactions/reposts
    replies = db.query(models.Post).filter(models.Post.reply_to_id == post_id).all()
    for reply in replies:
        reply_repost_ids = [r.id for r in reply.reposts]
        if reply_repost_ids:
            db.query(models.Reaction).filter(
                models.Reaction.target_type == "repost",
                models.Reaction.target_id.in_(reply_repost_ids),
            ).delete(synchronize_session=False)
        db.query(models.Reaction).filter(
            models.Reaction.target_type == "post",
            models.Reaction.target_id == reply.id,
        ).delete(synchronize_session=False)
        db.delete(reply)

    repost_ids = [r.id for r in post.reposts]
    if repost_ids:
        db.query(models.Reaction).filter(
            models.Reaction.target_type == "repost",
            models.Reaction.target_id.in_(repost_ids),
        ).delete(synchronize_session=False)
    db.query(models.Reaction).filter(
        models.Reaction.target_type == "post",
        models.Reaction.target_id == post_id,
    ).delete(synchronize_session=False)

    db.delete(post)
    db.commit()
    return {"message": f"post {post_id} deleted"}


def list_all_reposts(
    db: Session,
    user_id: int = None,
    sort_by: str = "created_at",
    order: str = "desc",
    skip: int = 0,
    limit: int = 20,
):
    query = db.query(models.Repost)
    if user_id:
        query = query.filter(models.Repost.user_id == user_id)
    total = query.count()
    col = _REPOST_SORT.get(sort_by, models.Repost.created_at)
    reposts = (
        query
        .order_by(col.desc() if order == "desc" else col.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"total": total, "skip": skip, "limit": limit, "items": [_fmt_repost(db, r) for r in reposts]}


def update_repost(db: Session, repost_id: int, data: "schemas.RepostUpdate", current_user: models.User):
    repost = db.query(models.Repost).filter(models.Repost.id == repost_id).first()
    if not repost:
        raise HTTPException(status_code=404, detail="Repost not found")
    if repost.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    repost.comment = data.comment
    db.commit()
    db.refresh(repost)
    return _fmt_repost(db, repost)


# ---- Repost ----

def list_reposts(
    db: Session,
    post_id: int,
    sort_by: str = "created_at",
    order: str = "desc",
    skip: int = 0,
    limit: int = 20,
):
    if not db.query(models.Post).filter(models.Post.id == post_id).first():
        raise HTTPException(status_code=404, detail="Post not found")

    query = db.query(models.Repost).filter(models.Repost.post_id == post_id)
    total = query.count()
    col = _REPOST_SORT.get(sort_by, models.Repost.created_at)
    reposts = (
        query
        .order_by(col.desc() if order == "desc" else col.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"total": total, "skip": skip, "limit": limit, "items": [_fmt_repost(db, r) for r in reposts]}


def create_repost(db: Session, post_id: int, data: schemas.RepostCreate, current_user: models.User):
    if not db.query(models.Post).filter(models.Post.id == post_id).first():
        raise HTTPException(status_code=404, detail="Post not found")
    repost = models.Repost(user_id=current_user.id, post_id=post_id, comment=data.comment)
    db.add(repost)
    db.commit()
    db.refresh(repost)
    return _fmt_repost(db, repost)


def delete_repost(db: Session, repost_id: int, current_user: models.User):
    repost = db.query(models.Repost).filter(models.Repost.id == repost_id).first()
    if not repost:
        raise HTTPException(status_code=404, detail="Repost not found")
    if repost.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    db.query(models.Reaction).filter(
        models.Reaction.target_type == "repost",
        models.Reaction.target_id == repost_id,
    ).delete(synchronize_session=False)
    db.delete(repost)
    db.commit()
    return {"message": f"repost {repost_id} deleted"}


# ---- Reaction ----

def react(
    db: Session,
    target_type: str,
    target_id: int,
    data: schemas.ReactionCreate,
    current_user: models.User,
):
    if data.reaction not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="reaction must be 'like' or 'dislike'")

    if target_type == "post":
        obj = db.query(models.Post).filter(models.Post.id == target_id).first()
    else:
        obj = db.query(models.Repost).filter(models.Repost.id == target_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"{target_type.capitalize()} not found")
    if obj.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot react to your own content")

    existing = db.query(models.Reaction).filter(
        models.Reaction.user_id == current_user.id,
        models.Reaction.target_type == target_type,
        models.Reaction.target_id == target_id,
    ).first()

    if existing:
        if existing.reaction == data.reaction:
            db.delete(existing)
            db.commit()
            return {"message": "reaction removed"}
        existing.reaction = data.reaction
        db.commit()
        db.refresh(existing)
        return existing

    reaction = models.Reaction(
        user_id=current_user.id,
        target_type=target_type,
        target_id=target_id,
        reaction=data.reaction,
    )
    db.add(reaction)
    db.commit()
    db.refresh(reaction)
    return reaction
