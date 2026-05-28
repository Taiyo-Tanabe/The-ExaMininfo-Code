from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas


def _fmt_review(db: Session, rv: models.Review) -> dict:
    user   = db.query(models.User).filter(models.User.id == rv.user_id).first()
    school = db.query(models.School).filter(models.School.id == rv.school_id).first()
    return {
        "id":              rv.id,
        "user_id":                rv.user_id,
        "user_name":              user.name       if user else None,
        "user_avatar_url":        user.avatar_url if user else None,
        "user_avatar_position_x": user.avatar_position_x if user else 50,
        "user_avatar_position_y": user.avatar_position_y if user else 50,
        "school_id":       rv.school_id,
        "school_name":     school.name if school else None,
        "rating":          rv.rating,
        "comment":         rv.comment,
        "course_name":     rv.course_name,
        "created_at":      rv.created_at,
    }


def list_reviews(db: Session, school_id: int, skip: int = 0, limit: int = 20):
    if not db.query(models.School).filter(models.School.id == school_id).first():
        raise HTTPException(status_code=404, detail="School not found")
    query = db.query(models.Review).filter(models.Review.school_id == school_id)
    total = query.count()
    items = query.order_by(models.Review.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": [_fmt_review(db, r) for r in items]}


def list_all_reviews(db: Session, school_name: str = None, skip: int = 0, limit: int = 50):
    query = db.query(models.Review)
    if school_name:
        query = query.join(models.School, models.Review.school_id == models.School.id).filter(
            models.School.name.ilike(f"%{school_name}%")
        )
    total = query.count()
    items = query.order_by(models.Review.created_at.desc()).offset(skip).limit(limit).all()
    reviews = []
    for rv in items:
        school = db.query(models.School).filter(models.School.id == rv.school_id).first()
        d = _fmt_review(db, rv)
        d["school_name"] = school.name if school else None
        reviews.append(d)
    return {"total": total, "skip": skip, "limit": limit, "items": reviews}


def list_user_reviews(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    query = db.query(models.Review).filter(models.Review.user_id == user_id)
    total = query.count()
    items = query.order_by(models.Review.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": [_fmt_review(db, r) for r in items]}


def create_review(db: Session, school_id: int, data: schemas.ReviewCreate, current_user: models.User):
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="rating must be between 1 and 5")
    if not db.query(models.School).filter(models.School.id == school_id).first():
        raise HTTPException(status_code=404, detail="School not found")

    existing = db.query(models.Review).filter(
        models.Review.user_id == current_user.id,
        models.Review.school_id == school_id,
    ).first()

    if existing:
        existing.rating      = data.rating
        existing.comment     = data.comment
        existing.course_name = data.course_name
        db.commit()
        db.refresh(existing)
        return _fmt_review(db, existing)

    review = models.Review(
        user_id=current_user.id,
        school_id=school_id,
        rating=data.rating,
        comment=data.comment,
        course_name=data.course_name,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return _fmt_review(db, review)


def delete_review(db: Session, review_id: int, current_user: models.User):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(review)
    db.commit()
    return {"message": f"review {review_id} deleted"}
