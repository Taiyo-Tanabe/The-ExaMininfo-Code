from datetime import date as date_cls

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models, schemas


def _compute_occurred_date(year, month, day):
    if year and month and day:
        try:
            return date_cls(year, month, day)
        except ValueError:
            pass
    return None


def _reaction_counts(db: Session, incident_id: int) -> dict:
    rows = db.query(models.Reaction).filter(
        models.Reaction.target_type == "incident",
        models.Reaction.target_id == incident_id,
    ).all()
    return {
        "like_count":    sum(1 for r in rows if r.reaction == "like"),
        "dislike_count": sum(1 for r in rows if r.reaction == "dislike"),
    }


def _fmt_incident(db: Session, inc: models.Incident) -> dict:
    counts = _reaction_counts(db, inc.id)
    comment_count = db.query(models.Post).filter(
        models.Post.incident_id == inc.id,
        models.Post.reply_to_id == None,
    ).count()
    user   = db.query(models.User).filter(models.User.id == inc.user_id).first() if inc.user_id else None
    school = db.query(models.School).filter(models.School.id == inc.school_id).first()
    return {
        "id":           inc.id,
        "title":        inc.title,
        "description":  inc.description,
        "course_name":  inc.course_name,
        "school_id":    inc.school_id,
        "school_name":  school.name if school else None,
        "user_id":                inc.user_id,
        "user_name":              user.name       if user else None,
        "user_avatar_url":        user.avatar_url if user else None,
        "user_avatar_position_x": user.avatar_position_x if user else 50,
        "user_avatar_position_y": user.avatar_position_y if user else 50,
        "created_at":   inc.created_at,
        "occurred_date":  inc.occurred_date,
        "occurred_year":  inc.occurred_year,
        "occurred_month": inc.occurred_month,
        "occurred_day":   inc.occurred_day,
        "comment_count":  comment_count,
        **counts,
    }


_SORT = {
    "title":         models.Incident.title,
    "created_at":    models.Incident.created_at,
    "occurred_date": models.Incident.occurred_date,
}


def list_incidents(
    db: Session,
    school_id: int = None,
    q: str = None,
    school_name: str = None,
    user_id: int = None,
    sort_by: str = "created_at",
    order: str = "desc",
    skip: int = 0,
    limit: int = 20,
):
    query = db.query(models.Incident)
    if school_id:
        query = query.filter(models.Incident.school_id == school_id)
    if user_id:
        query = query.filter(models.Incident.user_id == user_id)
    if school_name:
        query = query.join(models.School, models.Incident.school_id == models.School.id).filter(
            models.School.name.ilike(f"%{school_name}%")
        )
    if q:
        query = query.filter(
            or_(
                models.Incident.title.ilike(f"%{q}%"),
                models.Incident.description.ilike(f"%{q}%"),
            )
        )

    total = query.count()
    col = _SORT.get(sort_by, models.Incident.created_at)
    items = (
        query
        .order_by(col.desc() if order == "desc" else col.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"total": total, "skip": skip, "limit": limit, "items": [_fmt_incident(db, i) for i in items]}


def get_incident(db: Session, incident_id: int):
    inc = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _fmt_incident(db, inc)


def create_incident(db: Session, data: schemas.IncidentCreate, current_user: models.User):
    school = db.query(models.School).filter(models.School.id == data.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    fields = data.model_dump()
    fields["occurred_date"] = _compute_occurred_date(
        fields.get("occurred_year"), fields.get("occurred_month"), fields.get("occurred_day")
    )
    fields["user_id"] = current_user.id
    incident = models.Incident(**fields)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return _fmt_incident(db, incident)


def update_incident(db: Session, incident_id: int, data: schemas.IncidentCreate, current_user: models.User):
    inc = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    if inc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    fields = data.model_dump()
    fields["occurred_date"] = _compute_occurred_date(
        fields.get("occurred_year"), fields.get("occurred_month"), fields.get("occurred_day")
    )
    for k, v in fields.items():
        setattr(inc, k, v)
    db.commit()
    db.refresh(inc)
    return _fmt_incident(db, inc)


def delete_incident(db: Session, incident_id: int, current_user: models.User):
    inc = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    if inc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(inc)
    db.commit()
    return {"message": f"incident {incident_id} deleted"}


def react_to_incident(db: Session, incident_id: int, data: schemas.ReactionCreate, current_user: models.User):
    if data.reaction not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="reaction must be 'like' or 'dislike'")
    if not db.query(models.Incident).filter(models.Incident.id == incident_id).first():
        raise HTTPException(status_code=404, detail="Incident not found")

    existing = db.query(models.Reaction).filter(
        models.Reaction.user_id == current_user.id,
        models.Reaction.target_type == "incident",
        models.Reaction.target_id == incident_id,
    ).first()

    if existing:
        if existing.reaction == data.reaction:
            db.delete(existing); db.commit()
            return {"message": "reaction removed"}
        existing.reaction = data.reaction; db.commit()
        return {"message": "reaction updated"}

    reaction = models.Reaction(
        user_id=current_user.id, target_type="incident",
        target_id=incident_id, reaction=data.reaction,
    )
    db.add(reaction); db.commit()
    return {"message": "reaction added"}
