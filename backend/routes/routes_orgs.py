import io, base64
from typing import Optional, List
from fastapi import APIRouter, Body, Depends, Query, Request, UploadFile, File, HTTPException
from PIL import Image
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas, models
from ..auth import get_current_user, verify_token
from ..functions.functions_orgs import (
    list_orgs, get_org, create_org, update_org, delete_org,
    list_members, join_org, leave_org, update_member, remove_member,
    _is_org_admin,
)

router = APIRouter(prefix="/orgs", tags=["Organizations"])


def _optional_user(request: Request, db: Session = Depends(get_db)) -> Optional[models.User]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        user_id = verify_token(auth[7:])
        return db.query(models.User).filter(models.User.id == int(user_id)).first()
    except Exception:
        return None


@router.get("/", response_model=schemas.Page[schemas.OrgOut])
def list_orgs_route(
    skip: int = 0, limit: int = 50, q: str = Query(""),
    school_id: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    my_orgs: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(_optional_user),
):
    return list_orgs(db, skip, limit, q, school_id, department, my_orgs, current_user)


@router.post("/", response_model=schemas.OrgOut)
def create_org_route(
    data: schemas.OrgCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_org(db, data, current_user.id)


@router.get("/{org_id}", response_model=schemas.OrgOut)
def get_org_route(
    org_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(_optional_user),
):
    return get_org(db, org_id, current_user)


@router.patch("/{org_id}", response_model=schemas.OrgOut)
def update_org_route(
    org_id: int, data: schemas.OrgUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_org(db, org_id, data, current_user)


@router.post("/{org_id}/icon")
def upload_org_icon_route(
    org_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="団体が見つかりません")
    if not _is_org_admin(org, current_user, db):
        raise HTTPException(status_code=403, detail="権限がありません")
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="jpeg/png/webp/gifのみ対応しています")
    data = file.file.read()
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((256, 256), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    org.icon_url = f"data:image/jpeg;base64,{b64}"
    db.commit()
    db.refresh(org)
    return {"icon_url": org.icon_url}


@router.delete("/{org_id}")
def delete_org_route(
    org_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return delete_org(db, org_id, current_user)


# ── メンバー ──────────────────────────────────────────────────────────

@router.get("/{org_id}/members", response_model=List[schemas.OrgMemberOut])
def list_members_route(
    org_id: int,
    status: Optional[str] = Query(None),  # "pending" | "approved" | None（全件）
    db: Session = Depends(get_db),
):
    return list_members(db, org_id, status)


@router.post("/{org_id}/join", response_model=schemas.OrgMemberOut)
def join_org_route(
    org_id: int,
    data: schemas.JoinOrgRequest = Body(default=schemas.JoinOrgRequest()),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return join_org(db, org_id, current_user, data.personal_info)


@router.delete("/{org_id}/leave")
def leave_org_route(
    org_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return leave_org(db, org_id, current_user)


@router.patch("/{org_id}/members/{user_id}", response_model=schemas.OrgMemberOut)
def update_member_route(
    org_id: int, user_id: int,
    data: schemas.OrgMemberUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_member(db, org_id, user_id, data, current_user)


@router.delete("/{org_id}/members/{user_id}")
def remove_member_route(
    org_id: int, user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return remove_member(db, org_id, user_id, current_user)
