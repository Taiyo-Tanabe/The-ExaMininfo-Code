from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas


def _to_out(org: models.Organization, current_user: models.User | None = None) -> dict:
    my_role = None
    if current_user:
        if org.created_by == current_user.id:
            my_role = "creator"
        else:
            for m in org.members:
                if m.user_id == current_user.id:
                    if m.status == "approved":
                        my_role = m.role
                    else:
                        my_role = "pending"
                    break

    approved_count = sum(1 for m in org.members if m.status == "approved")
    c = org.creator

    return {
        "id": org.id,
        "name": org.name,
        "description": org.description,
        "school_id": org.school_id,
        "school_name": org.school.name if org.school else None,
        "department": org.department,
        "created_by": org.created_by,
        "creator_name": c.name if c else None,
        "creator_avatar_url": c.avatar_url if c else None,
        "creator_avatar_position_x": c.avatar_position_x if c else 50,
        "creator_avatar_position_y": c.avatar_position_y if c else 50,
        "created_at": org.created_at,
        "event_count": len(org.events),
        "member_count": approved_count,
        "my_role": my_role,
        "personal_info_prompt": org.personal_info_prompt,
        "icon_url": org.icon_url,
        "icon_position_x": org.icon_position_x if org.icon_position_x is not None else 50,
        "icon_position_y": org.icon_position_y if org.icon_position_y is not None else 50,
    }


def _member_out(m: models.OrgMember) -> dict:
    u = m.user
    return {
        "id": m.id,
        "org_id": m.org_id,
        "user_id": m.user_id,
        "user_name": u.name if u else None,
        "user_avatar_url": u.avatar_url if u else None,
        "user_avatar_position_x": u.avatar_position_x if u else 50,
        "user_avatar_position_y": u.avatar_position_y if u else 50,
        "role": m.role,
        "status": m.status,
        "personal_info": m.personal_info,
        "joined_at": m.joined_at,
    }


def _is_org_admin(org: models.Organization, user: models.User, db: Session) -> bool:
    if org.created_by == user.id:
        return True
    member = db.query(models.OrgMember).filter(
        models.OrgMember.org_id == org.id,
        models.OrgMember.user_id == user.id,
        models.OrgMember.role == "admin",
        models.OrgMember.status == "approved",
    ).first()
    return member is not None


def list_orgs(db: Session, skip: int, limit: int, q: str,
              school_id: int | None = None,
              department: str | None = None,
              my_orgs: bool = False,
              current_user: models.User | None = None) -> dict:
    query = db.query(models.Organization)
    if q:
        query = query.filter(models.Organization.name.ilike(f"%{q}%"))
    if school_id:
        query = query.filter(models.Organization.school_id == school_id)
    if department:
        query = query.filter(models.Organization.department.ilike(f"%{department}%"))
    if my_orgs and current_user:
        creator_ids = {o.id for o in current_user.created_organizations}
        member_ids  = {m.org_id for m in current_user.org_memberships if m.status == "approved"}
        all_ids = creator_ids | member_ids
        if not all_ids:
            return {"total": 0, "skip": skip, "limit": limit, "items": []}
        query = query.filter(models.Organization.id.in_(all_ids))

    total = query.count()
    items = query.order_by(models.Organization.name.asc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit,
            "items": [_to_out(o, current_user) for o in items]}


def get_org(db: Session, org_id: int, current_user: models.User | None = None) -> dict:
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="団体が見つかりません")
    return _to_out(org, current_user)


def create_org(db: Session, data: schemas.OrgCreate, creator_id: int) -> dict:
    if db.query(models.Organization).filter(models.Organization.name == data.name).first():
        raise HTTPException(status_code=400, detail="同じ名前の団体がすでに存在します")
    org = models.Organization(
        name=data.name,
        description=data.description,
        school_id=data.school_id,
        department=data.department,
        personal_info_prompt=data.personal_info_prompt,
        created_by=creator_id,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return _to_out(org)


def update_org(db: Session, org_id: int, data: schemas.OrgUpdate,
               current_user: models.User) -> dict:
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="団体が見つかりません")
    if not _is_org_admin(org, current_user, db):
        raise HTTPException(status_code=403, detail="編集権限がありません")
    if data.name is not None and data.name != org.name:
        if db.query(models.Organization).filter(models.Organization.name == data.name).first():
            raise HTTPException(status_code=400, detail="同じ名前の団体がすでに存在します")
        org.name = data.name
    if data.description is not None:
        org.description = data.description
    if data.school_id is not None:
        org.school_id = data.school_id
    if data.department is not None:
        org.department = data.department
    if 'personal_info_prompt' in data.model_fields_set:
        org.personal_info_prompt = data.personal_info_prompt
    if data.icon_position_x is not None:
        org.icon_position_x = data.icon_position_x
    if data.icon_position_y is not None:
        org.icon_position_y = data.icon_position_y
    db.commit()
    db.refresh(org)
    return _to_out(org, current_user)


def delete_org(db: Session, org_id: int, current_user: models.User) -> dict:
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="団体が見つかりません")
    if org.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="削除権限がありません")
    db.delete(org)
    db.commit()
    return {"message": f"org {org_id} deleted"}


# ── メンバー管理 ──────────────────────────────────────────────────────

def list_members(db: Session, org_id: int, status: str | None = None) -> list:
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="団体が見つかりません")
    query = (db.query(models.OrgMember)
               .filter(models.OrgMember.org_id == org_id)
               .order_by(models.OrgMember.joined_at.asc()))
    if status:
        query = query.filter(models.OrgMember.status == status)
    return [_member_out(m) for m in query.all()]


def join_org(db: Session, org_id: int, current_user: models.User,
             personal_info: str | None = None) -> dict:
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="団体が見つかりません")
    if org.created_by == current_user.id:
        raise HTTPException(status_code=400, detail="作成者は加入不要です")
    existing = db.query(models.OrgMember).filter(
        models.OrgMember.org_id == org_id,
        models.OrgMember.user_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=400,
            detail="承認待ちです" if existing.status == "pending" else "すでにメンバーです")
    member = models.OrgMember(
        org_id=org_id, user_id=current_user.id,
        role="member", status="pending",
        personal_info=personal_info,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return _member_out(member)


def leave_org(db: Session, org_id: int, current_user: models.User) -> dict:
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="団体が見つかりません")
    if org.created_by == current_user.id:
        raise HTTPException(status_code=400, detail="作成者は退会できません")
    member = db.query(models.OrgMember).filter(
        models.OrgMember.org_id == org_id,
        models.OrgMember.user_id == current_user.id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="メンバーではありません")
    db.delete(member)
    db.commit()
    return {"message": "left"}


def update_member(db: Session, org_id: int, target_user_id: int,
                  data: schemas.OrgMemberUpdate, current_user: models.User) -> dict:
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="団体が見つかりません")
    if not _is_org_admin(org, current_user, db):
        raise HTTPException(status_code=403, detail="権限がありません")
    if org.created_by == target_user_id and data.role is not None:
        raise HTTPException(status_code=400, detail="作成者のロールは変更できません")

    member = db.query(models.OrgMember).filter(
        models.OrgMember.org_id == org_id,
        models.OrgMember.user_id == target_user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="メンバーが見つかりません")

    if data.role is not None:
        if data.role not in ("member", "admin"):
            raise HTTPException(status_code=400, detail="role は 'member' か 'admin'")
        member.role = data.role
    if data.status is not None:
        if data.status != "approved":
            raise HTTPException(status_code=400, detail="status は 'approved' のみ指定可")
        member.status = data.status

    db.commit()
    db.refresh(member)
    return _member_out(member)


def remove_member(db: Session, org_id: int, target_user_id: int,
                  current_user: models.User) -> dict:
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="団体が見つかりません")
    if not _is_org_admin(org, current_user, db):
        raise HTTPException(status_code=403, detail="権限がありません")
    if org.created_by == target_user_id:
        raise HTTPException(status_code=400, detail="作成者は削除できません")
    member = db.query(models.OrgMember).filter(
        models.OrgMember.org_id == org_id,
        models.OrgMember.user_id == target_user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="メンバーが見つかりません")
    db.delete(member)
    db.commit()
    return {"message": "removed"}
