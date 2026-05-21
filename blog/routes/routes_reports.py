from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas, models
from ..auth import get_current_user
from ..functions.functions_reports import (
    create_report,
    list_reports,
    delete_report,
    delete_reported_content,
)

router = APIRouter(tags=["Reports"])


@router.post("/reports/", response_model=schemas.ReportOut)
def create_report_route(
    data: schemas.ReportCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return create_report(db, data, current_user)


@router.get("/reports/", response_model=schemas.Page[schemas.ReportOut])
def list_reports_route(
    target_type: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin only")
    return list_reports(db, target_type=target_type, skip=skip, limit=limit)


@router.delete("/reports/{report_id}")
def delete_report_route(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin only")
    return delete_report(db, report_id, current_user)


@router.delete("/reports/content/{target_type}/{target_id}")
def delete_reported_content_route(
    target_type: str,
    target_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin only")
    return delete_reported_content(db, target_type, target_id, current_user)
