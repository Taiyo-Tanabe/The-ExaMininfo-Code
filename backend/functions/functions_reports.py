from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas


def _fmt_report(db: Session, report: models.Report) -> dict:
    reporter = db.query(models.User).filter(models.User.id == report.reporter_id).first()
    return {
        "id":            report.id,
        "reporter_id":   report.reporter_id,
        "reporter_name": reporter.name if reporter else None,
        "target_type":   report.target_type,
        "target_id":     report.target_id,
        "reason":        report.reason,
        "created_at":    report.created_at,
    }


def create_report(db: Session, data: schemas.ReportCreate, current_user: models.User):
    if data.target_type not in ("post", "repost", "incident", "review"):
        raise HTTPException(status_code=400, detail="Invalid target_type")

    existing = db.query(models.Report).filter(
        models.Report.reporter_id == current_user.id,
        models.Report.target_type == data.target_type,
        models.Report.target_id == data.target_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already reported")

    report = models.Report(
        reporter_id=current_user.id,
        target_type=data.target_type,
        target_id=data.target_id,
        reason=data.reason,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return _fmt_report(db, report)


def list_reports(
    db: Session,
    target_type: str = None,
    skip: int = 0,
    limit: int = 50,
):
    query = db.query(models.Report)
    if target_type:
        query = query.filter(models.Report.target_type == target_type)
    total = query.count()
    items = (
        query
        .order_by(models.Report.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"total": total, "skip": skip, "limit": limit, "items": [_fmt_report(db, r) for r in items]}


def delete_report(db: Session, report_id: int, current_user: models.User):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(report)
    db.commit()
    return {"message": f"report {report_id} deleted"}


def delete_reported_content(db: Session, target_type: str, target_id: int, current_user: models.User):
    if target_type == "post":
        obj = db.query(models.Post).filter(models.Post.id == target_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail="Post not found")
        db.query(models.Report).filter(
            models.Report.target_type == target_type,
            models.Report.target_id == target_id,
        ).delete(synchronize_session=False)
        db.delete(obj)
    elif target_type == "repost":
        obj = db.query(models.Repost).filter(models.Repost.id == target_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail="Repost not found")
        db.query(models.Reaction).filter(
            models.Reaction.target_type == "repost",
            models.Reaction.target_id == target_id,
        ).delete(synchronize_session=False)
        db.query(models.Report).filter(
            models.Report.target_type == target_type,
            models.Report.target_id == target_id,
        ).delete(synchronize_session=False)
        db.delete(obj)
    elif target_type == "incident":
        obj = db.query(models.Incident).filter(models.Incident.id == target_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail="Incident not found")
        db.query(models.Report).filter(
            models.Report.target_type == target_type,
            models.Report.target_id == target_id,
        ).delete(synchronize_session=False)
        db.delete(obj)
    elif target_type == "review":
        obj = db.query(models.Review).filter(models.Review.id == target_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail="Review not found")
        db.query(models.Report).filter(
            models.Report.target_type == target_type,
            models.Report.target_id == target_id,
        ).delete(synchronize_session=False)
        db.delete(obj)
    else:
        raise HTTPException(status_code=400, detail="Invalid target_type")
    db.commit()
    return {"message": "content deleted"}
