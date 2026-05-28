from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas

_SORT = {
    "name":       models.School.name,
    "prefecture": models.School.prefecture,
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


def _fmt_course(db: Session, course: models.Course) -> dict:
    counts = _reaction_counts(db, "course", course.id)
    return {
        "id": course.id, "name": course.name,
        "school_id": course.school_id, "deviation": course.deviation,
        **counts,
    }


def _fmt_school(db: Session, school: models.School) -> dict:
    counts = _reaction_counts(db, "school", school.id)
    return {
        "id": school.id, "name": school.name, "yomi": school.yomi,
        "prefecture": school.prefecture, "prefecture_yomi": school.prefecture_yomi,
        "courses": [_fmt_course(db, c) for c in school.courses],
        **counts,
    }


def list_schools(
    db: Session,
    q: str = None,
    prefecture: str = None,
    sort_by: str = "name",
    order: str = "asc",
    skip: int = 0,
    limit: int = 20,
):
    from sqlalchemy import or_, case
    query = db.query(models.School)
    if prefecture:
        query = query.filter(or_(
            models.School.prefecture.ilike(f"%{prefecture}%"),
            models.School.prefecture_yomi.ilike(f"%{prefecture}%"),
        ))
    if q:
        query = query.filter(or_(
            models.School.name.ilike(f"%{q}%"),
            models.School.yomi.ilike(f"%{q}%"),
        ))

    total = query.count()

    if q:
        # 完全一致 → 前方一致 → 部分一致 の順で優先表示
        priority = case(
            (models.School.name.ilike(q),        0),
            (models.School.name.ilike(f"{q}%"),  1),
            else_=2,
        )
        items = (
            query
            .options(joinedload(models.School.courses))
            .order_by(priority, models.School.name.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    else:
        col = _SORT.get(sort_by, models.School.name)
        items = (
            query
            .options(joinedload(models.School.courses))
            .order_by(col.desc() if order == "desc" else col.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    return {"total": total, "skip": skip, "limit": limit, "items": items}


def get_school(db: Session, school_id: int):
    school = (
        db.query(models.School)
        .options(joinedload(models.School.courses))
        .filter(models.School.id == school_id)
        .first()
    )
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return _fmt_school(db, school)


def react_to_school(db: Session, school_id: int, data: schemas.ReactionCreate, current_user: models.User):
    if data.reaction not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="reaction must be 'like' or 'dislike'")
    if not db.query(models.School).filter(models.School.id == school_id).first():
        raise HTTPException(status_code=404, detail="School not found")

    existing = db.query(models.Reaction).filter(
        models.Reaction.user_id == current_user.id,
        models.Reaction.target_type == "school",
        models.Reaction.target_id == school_id,
    ).first()

    if existing:
        if existing.reaction == data.reaction:
            db.delete(existing); db.commit()
            return {"message": "reaction removed"}
        existing.reaction = data.reaction; db.commit()
        return {"message": "reaction updated"}

    reaction = models.Reaction(
        user_id=current_user.id, target_type="school",
        target_id=school_id, reaction=data.reaction,
    )
    db.add(reaction); db.commit()
    return {"message": "reaction added"}


def create_school(db: Session, data: schemas.SchoolCreate):
    school = models.School(**data.model_dump())
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def update_school(db: Session, school_id: int, data: schemas.SchoolCreate):
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    for k, v in data.model_dump().items():
        setattr(school, k, v)
    db.commit()
    db.refresh(school)
    return school


def delete_school(db: Session, school_id: int):
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    db.delete(school)
    db.commit()
    return {"message": f"school {school_id} deleted"}
