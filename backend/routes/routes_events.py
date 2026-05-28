from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas, models
from ..auth import get_current_user, verify_token
from ..functions.functions_events import (
    list_events, get_event, create_event, update_event, delete_event,
    upsert_attendance, cancel_attendance, list_attendees, approve_attendance,
    request_view, list_view_requests, handle_view_request,
)

router = APIRouter(prefix="/events", tags=["Events"])


def _optional_user(request: Request, db: Session = Depends(get_db)) -> Optional[models.User]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        user_id = verify_token(auth[7:])
        return db.query(models.User).filter(models.User.id == int(user_id)).first()
    except Exception:
        return None


# ── イベント CRUD ─────────────────────────────────────────────────────

@router.get("/", response_model=schemas.Page[schemas.EventOut])
def list_events_route(
    skip: int = 0,
    limit: int = 50,
    org_id: Optional[int] = Query(None),
    school_id: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    my_orgs: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(_optional_user),
):
    return list_events(db, skip, limit, org_id, school_id, department, my_orgs, current_user)


@router.post("/", response_model=schemas.EventOut)
def create_event_route(
    data: schemas.EventCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_event(db, data, current_user)


@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event_route(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(_optional_user),
):
    return get_event(db, event_id, current_user)


@router.patch("/{event_id}", response_model=schemas.EventOut)
def update_event_route(
    event_id: int,
    data: schemas.EventUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_event(db, event_id, data, current_user)


@router.delete("/{event_id}")
def delete_event_route(
    event_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return delete_event(db, event_id, current_user)


# ── 参加登録 ─────────────────────────────────────────────────────────

@router.put("/{event_id}/attend", response_model=schemas.AttendanceOut)
def upsert_attendance_route(
    event_id: int,
    data: schemas.AttendanceUpsert,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return upsert_attendance(db, event_id, data, current_user)


@router.delete("/{event_id}/attend")
def cancel_attendance_route(
    event_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return cancel_attendance(db, event_id, current_user)


@router.get("/{event_id}/attendees", response_model=list[schemas.AttendanceOut])
def list_attendees_route(
    event_id: int,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return list_attendees(db, event_id, status)


@router.patch("/{event_id}/attendees/{target_user_id}", response_model=schemas.AttendanceOut)
def approve_attendance_route(
    event_id: int,
    target_user_id: int,
    action: schemas.AttendanceAction,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return approve_attendance(db, event_id, target_user_id, action, current_user)


# ── 閲覧申請 ─────────────────────────────────────────────────────────

@router.post("/{event_id}/view-request", response_model=schemas.ViewRequestOut)
def request_view_route(
    event_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return request_view(db, event_id, current_user)


@router.get("/{event_id}/view-requests", response_model=list[schemas.ViewRequestOut])
def list_view_requests_route(
    event_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return list_view_requests(db, event_id, current_user)


@router.patch("/{event_id}/view-requests/{target_user_id}", response_model=schemas.ViewRequestOut)
def handle_view_request_route(
    event_id: int,
    target_user_id: int,
    action: schemas.ViewRequestAction,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return handle_view_request(db, event_id, target_user_id, action, current_user)
