from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas

_SORT = {
    "name":      models.Course.name,
    "deviation": models.Course.deviation,
}


def list_courses(
    db: Session,
    school_id: int = None,
    q: str = None,
    sort_by: str = "deviation",
    order: str = "desc",
    skip: int = 0,
    limit: int = 20,
):
    query = db.query(models.Course)
    if school_id:
        query = query.filter(models.Course.school_id == school_id)
    if q:
        query = query.filter(models.Course.name.ilike(f"%{q}%"))

    total = query.count()
    col = _SORT.get(sort_by, models.Course.deviation)
    items = (
        query
        .order_by(col.desc() if order == "desc" else col.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"total": total, "skip": skip, "limit": limit, "items": items}


def get_course(db: Session, course_id: int):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def react_to_course(db: Session, course_id: int, data: schemas.ReactionCreate, current_user: models.User):
    if data.reaction not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="reaction must be 'like' or 'dislike'")
    if not db.query(models.Course).filter(models.Course.id == course_id).first():
        raise HTTPException(status_code=404, detail="Course not found")

    existing = db.query(models.Reaction).filter(
        models.Reaction.user_id == current_user.id,
        models.Reaction.target_type == "course",
        models.Reaction.target_id == course_id,
    ).first()

    if existing:
        if existing.reaction == data.reaction:
            db.delete(existing); db.commit()
            return {"message": "reaction removed"}
        existing.reaction = data.reaction; db.commit()
        return {"message": "reaction updated"}

    reaction = models.Reaction(
        user_id=current_user.id, target_type="course",
        target_id=course_id, reaction=data.reaction,
    )
    db.add(reaction); db.commit()
    return {"message": "reaction added"}


def create_course(db: Session, data: schemas.CourseCreate):
    school = db.query(models.School).filter(models.School.id == data.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    course = models.Course(**data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def update_course(db: Session, course_id: int, data: schemas.CourseCreate):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for k, v in data.model_dump().items():
        setattr(course, k, v)
    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course_id: int):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return {"message": f"course {course_id} deleted"}
