from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas


# ── helpers ──────────────────────────────────────────────────────────

def _is_org_owner(event: models.Event, user: models.User) -> bool:
    if event.org_id and event.organization and event.organization.created_by == user.id:
        return True
    if event.created_by == user.id:
        return True
    if event.organization:
        for m in event.organization.members:
            if m.user_id == user.id and m.role == "admin" and m.status == "approved":
                return True
    return False


def _is_approved_member(event: models.Event, user_id: int) -> bool:
    """承認済みの団体メンバーか"""
    if event.organization:
        for m in event.organization.members:
            if m.user_id == user_id and m.status == "approved":
                return True
    return False


def _view_status(event: models.Event, user_id: int | None) -> str | None:
    if user_id is None:
        return None
    for r in event.view_requests:
        if r.user_id == user_id:
            return r.status
    return None


def _can_view_detail(event: models.Event, user: models.User | None) -> bool:
    if not event.requires_view_approval:
        return True
    if user is None:
        return False
    if _is_org_owner(event, user):
        return True
    # 承認済みメンバーかつ allow_member_view=true → 閲覧可
    if event.allow_member_view and _is_approved_member(event, user.id):
        return True
    return _view_status(event, user.id) == "approved"


def _to_out(event: models.Event, current_user: models.User | None) -> dict:
    uid = current_user.id if current_user else None
    can_view = _can_view_detail(event, current_user)
    can_manage = _is_org_owner(event, current_user) if current_user else False

    attending_count = sum(1 for a in event.attendances if a.status == "attending")

    my_status = None
    my_note = None
    if uid:
        for a in event.attendances:
            if a.user_id == uid:
                my_status = a.status
                my_note = a.note
                break

    my_view_req = _view_status(event, uid)

    base = {
        "id": event.id,
        # requires_view_approval=true かつ閲覧不可のとき title も非公開
        "title": event.title if can_view else None,
        "requires_view_approval": event.requires_view_approval,
        "requires_join_approval": event.requires_join_approval,
        "allow_member_view": event.allow_member_view,
        "allow_member_join": event.allow_member_join,
        "org_id": event.org_id,
        "org_name": event.organization.name if event.organization else None,
        "org_icon_url": event.organization.icon_url if event.organization else None,
        "org_icon_position_x": (event.organization.icon_position_x or 50) if event.organization else 50,
        "org_icon_position_y": (event.organization.icon_position_y or 50) if event.organization else 50,
        "start_at": event.start_at,
        "end_at": event.end_at,
        "created_by": event.created_by,
        "creator_name": event.creator.name if event.creator else None,
        "created_at": event.created_at,
        "attendee_count": attending_count,
        "my_status": my_status,
        "my_note": my_note,
        "my_view_request": my_view_req,
        "can_manage": can_manage,
    }

    if can_view:
        base.update({
            "description": event.description,
            "location": event.location,
            "max_participants": event.max_participants,
        })
    else:
        base.update({"description": None, "location": None, "max_participants": None})

    return base


# ── CRUD ─────────────────────────────────────────────────────────────

def list_events(db: Session, skip: int, limit: int,
                org_id: int | None, school_id: int | None, department: str | None,
                my_orgs: bool, current_user: models.User | None) -> dict:
    query = db.query(models.Event).order_by(models.Event.created_at.desc())

    if org_id:
        query = query.filter(models.Event.org_id == org_id)
    else:
        # 大学・学部フィルタ（Organization テーブルを JOIN）
        if school_id or department:
            query = query.join(
                models.Organization,
                models.Event.org_id == models.Organization.id,
            )
            if school_id:
                query = query.filter(models.Organization.school_id == school_id)
            if department:
                query = query.filter(
                    models.Organization.department.ilike(f"%{department}%")
                )

        # 自分の所属団体のみ
        if my_orgs:
            if not current_user:
                return {"total": 0, "skip": skip, "limit": limit, "items": []}
            creator_ids = {o.id for o in current_user.created_organizations}
            member_ids = {m.org_id for m in current_user.org_memberships if m.status == "approved"}
            all_ids = creator_ids | member_ids
            if not all_ids:
                return {"total": 0, "skip": skip, "limit": limit, "items": []}
            query = query.filter(models.Event.org_id.in_(all_ids))

    # requires_view_approval=true のイベントは閲覧可能なユーザーにのみ表示
    all_events = query.all()
    visible = [e for e in all_events if _can_view_detail(e, current_user)]
    total = len(visible)
    items = visible[skip: skip + limit]
    return {
        "total": total, "skip": skip, "limit": limit,
        "items": [_to_out(e, current_user) for e in items],
    }


def get_event(db: Session, event_id: int, current_user: models.User | None) -> dict:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    return _to_out(event, current_user)


def create_event(db: Session, data: schemas.EventCreate, creator: models.User) -> dict:
    org = db.query(models.Organization).filter(models.Organization.id == data.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="団体が見つかりません")
    # 団体オーナー・管理者メンバー・system admin のみ作成可
    is_allowed = (
        creator.role == "admin"
        or org.created_by == creator.id
        or db.query(models.OrgMember).filter(
            models.OrgMember.org_id == org.id,
            models.OrgMember.user_id == creator.id,
            models.OrgMember.role == "admin",
        ).first() is not None
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="この団体のイベントを作成する権限がありません")

    event = models.Event(
        org_id=data.org_id,
        title=data.title,
        description=data.description,
        location=data.location,
        start_at=data.start_at,
        end_at=data.end_at,
        max_participants=data.max_participants,
        requires_view_approval=data.requires_view_approval,
        requires_join_approval=data.requires_join_approval,
        created_by=creator.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return _to_out(event, creator)


def update_event(db: Session, event_id: int, data: schemas.EventUpdate,
                 current_user: models.User) -> dict:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    if not _is_org_owner(event, current_user):
        raise HTTPException(status_code=403, detail="編集権限がありません")

    for field in ("title", "description", "location", "start_at", "end_at",
                  "max_participants", "requires_view_approval", "requires_join_approval",
                  "allow_member_view", "allow_member_join"):
        val = getattr(data, field)
        if val is not None:
            setattr(event, field, val)

    db.commit()
    db.refresh(event)
    return _to_out(event, current_user)


def delete_event(db: Session, event_id: int, current_user: models.User) -> dict:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    if not _is_org_owner(event, current_user):
        raise HTTPException(status_code=403, detail="削除権限がありません")
    db.delete(event)
    db.commit()
    return {"message": f"event {event_id} deleted"}


# ── 参加登録 ──────────────────────────────────────────────────────────

def upsert_attendance(db: Session, event_id: int, data: schemas.AttendanceUpsert,
                      current_user: models.User) -> dict:
    if data.status not in ("attending", "not_attending"):
        raise HTTPException(status_code=400, detail="status は 'attending' か 'not_attending'")

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")

    # 閲覧承認が必要なイベントは、承認済みでないと参加申請不可
    if event.requires_view_approval and not _is_org_owner(event, current_user):
        if _view_status(event, current_user.id) != "approved":
            raise HTTPException(status_code=403, detail="閲覧が承認されていません")

    # 参加ステータスの決定
    # requires_join_approval=true でも allow_member_join=true の承認済みメンバーは直接参加
    resolved_status = data.status
    if data.status == "attending" and event.requires_join_approval and not _is_org_owner(event, current_user):
        member_can_join = event.allow_member_join and _is_approved_member(event, current_user.id)
        if not member_can_join:
            resolved_status = "pending"

    # 定員チェック（attending のみカウント）
    if resolved_status == "attending" and event.max_participants is not None:
        cur = sum(1 for a in event.attendances
                  if a.status == "attending" and a.user_id != current_user.id)
        if cur >= event.max_participants:
            raise HTTPException(status_code=409, detail="定員に達しています")

    attendance = (
        db.query(models.EventAttendance)
        .filter(models.EventAttendance.event_id == event_id,
                models.EventAttendance.user_id == current_user.id)
        .first()
    )
    if attendance:
        attendance.status = resolved_status
        attendance.note = data.note
    else:
        attendance = models.EventAttendance(
            event_id=event_id, user_id=current_user.id, status=resolved_status, note=data.note
        )
        db.add(attendance)

    db.commit()
    db.refresh(attendance)
    return _attendance_out(attendance)


def cancel_attendance(db: Session, event_id: int, current_user: models.User) -> dict:
    att = (db.query(models.EventAttendance)
           .filter(models.EventAttendance.event_id == event_id,
                   models.EventAttendance.user_id == current_user.id)
           .first())
    if not att:
        raise HTTPException(status_code=404, detail="参加登録が見つかりません")
    db.delete(att)
    db.commit()
    return {"message": "cancelled"}


def list_attendees(db: Session, event_id: int, status: str | None) -> list:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    query = db.query(models.EventAttendance).filter(models.EventAttendance.event_id == event_id)
    if status:
        query = query.filter(models.EventAttendance.status == status)
    return [_attendance_out(a) for a in query.all()]


def approve_attendance(db: Session, event_id: int, target_user_id: int,
                       action: schemas.AttendanceAction, current_user: models.User) -> dict:
    """pending → attending / rejected（団体オーナーのみ）"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    if not _is_org_owner(event, current_user):
        raise HTTPException(status_code=403, detail="承認権限がありません")
    if action.status not in ("attending", "rejected"):
        raise HTTPException(status_code=400, detail="status は 'attending' か 'rejected'")

    att = (db.query(models.EventAttendance)
           .filter(models.EventAttendance.event_id == event_id,
                   models.EventAttendance.user_id == target_user_id)
           .first())
    if not att:
        raise HTTPException(status_code=404, detail="申請が見つかりません")
    if att.status != "pending":
        raise HTTPException(status_code=400, detail="pending 状態の申請のみ変更できます")

    if action.status == "attending" and event.max_participants is not None:
        cur = sum(1 for a in event.attendances if a.status == "attending")
        if cur >= event.max_participants:
            raise HTTPException(status_code=409, detail="定員に達しています")

    att.status = action.status
    db.commit()
    db.refresh(att)
    return _attendance_out(att)


# ── 閲覧申請 ──────────────────────────────────────────────────────────

def request_view(db: Session, event_id: int, current_user: models.User) -> dict:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    if not event.requires_view_approval:
        raise HTTPException(status_code=400, detail="このイベントは承認不要です")
    if _is_org_owner(event, current_user):
        raise HTTPException(status_code=400, detail="団体オーナーは申請不要です")

    existing = (db.query(models.EventViewRequest)
                .filter(models.EventViewRequest.event_id == event_id,
                        models.EventViewRequest.user_id == current_user.id)
                .first())
    if existing:
        if existing.status == "approved":
            raise HTTPException(status_code=400, detail="すでに承認済みです")
        if existing.status == "pending":
            raise HTTPException(status_code=400, detail="すでに申請中です")
        # rejected → 再申請可
        existing.status = "pending"
        db.commit()
        db.refresh(existing)
        return _view_req_out(existing)

    req = models.EventViewRequest(event_id=event_id, user_id=current_user.id, status="pending")
    db.add(req)
    db.commit()
    db.refresh(req)
    return _view_req_out(req)


def list_view_requests(db: Session, event_id: int, current_user: models.User) -> list:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    if not _is_org_owner(event, current_user):
        raise HTTPException(status_code=403, detail="権限がありません")
    reqs = (db.query(models.EventViewRequest)
            .filter(models.EventViewRequest.event_id == event_id)
            .order_by(models.EventViewRequest.created_at.asc())
            .all())
    return [_view_req_out(r) for r in reqs]


def handle_view_request(db: Session, event_id: int, target_user_id: int,
                        action: schemas.ViewRequestAction, current_user: models.User) -> dict:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    if not _is_org_owner(event, current_user):
        raise HTTPException(status_code=403, detail="権限がありません")
    if action.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status は 'approved' か 'rejected'")

    req = (db.query(models.EventViewRequest)
           .filter(models.EventViewRequest.event_id == event_id,
                   models.EventViewRequest.user_id == target_user_id)
           .first())
    if not req:
        raise HTTPException(status_code=404, detail="申請が見つかりません")

    req.status = action.status
    db.commit()
    db.refresh(req)
    return _view_req_out(req)


# ── serializers ──────────────────────────────────────────────────────

def _attendance_out(a: models.EventAttendance) -> dict:
    return {
        "id": a.id,
        "event_id": a.event_id,
        "user_id": a.user_id,
        "user_name": a.user.name if a.user else None,
        "user_avatar_url": a.user.avatar_url if a.user else None,
        "status": a.status,
        "note": a.note,
        "created_at": a.created_at,
    }


def _view_req_out(r: models.EventViewRequest) -> dict:
    return {
        "id": r.id,
        "event_id": r.event_id,
        "user_id": r.user_id,
        "user_name": r.user.name if r.user else None,
        "status": r.status,
        "created_at": r.created_at,
    }
