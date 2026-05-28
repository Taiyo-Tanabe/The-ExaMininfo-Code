from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas
from ..auth import require_roles, get_current_user
from ..functions.functions_schools import (
    list_schools,
    get_school,
    react_to_school,
    create_school,
    update_school,
    delete_school,
)
from ..functions.functions_reviews import (
    list_reviews,
    list_all_reviews,
    create_review,
    delete_review,
)

router = APIRouter(prefix="/schools", tags=["Schools"])


@router.get("/", response_model=schemas.Page[schemas.SchoolOut])
def list_schools_route(
    q: str = None,
    prefecture: str = None,
    sort_by: str = "name",
    order: str = "asc",
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return list_schools(db, q, prefecture, sort_by, order, skip, limit)


@router.get("/{school_id}", response_model=schemas.SchoolOut)
def get_school_route(school_id: int, db: Session = Depends(get_db)):
    return get_school(db, school_id)


@router.post("/{school_id}/react")
def react_to_school_route(
    school_id: int,
    data: schemas.ReactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return react_to_school(db, school_id, data, current_user)


@router.post("/", response_model=schemas.SchoolOut)
def create_school_route(
    data: schemas.SchoolCreate,
    db: Session = Depends(get_db),
    _ = Depends(require_roles(["admin"])),
):
    return create_school(db, data)


@router.put("/{school_id}", response_model=schemas.SchoolOut)
def update_school_route(
    school_id: int,
    data: schemas.SchoolCreate,
    db: Session = Depends(get_db),
    _ = Depends(require_roles(["admin"])),
):
    return update_school(db, school_id, data)


@router.delete("/{school_id}")
def delete_school_route(
    school_id: int,
    db: Session = Depends(get_db),
    _ = Depends(require_roles(["admin"])),
):
    return delete_school(db, school_id)


@router.get("/reviews/", response_model=schemas.Page[schemas.ReviewOut])
def list_all_reviews_route(
    school_name: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _ = Depends(require_roles(["admin"])),
):
    return list_all_reviews(db, school_name, skip, limit)


@router.get("/{school_id}/reviews", response_model=schemas.Page[schemas.ReviewOut])
def list_reviews_route(
    school_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return list_reviews(db, school_id, skip, limit)


@router.post("/{school_id}/reviews", response_model=schemas.ReviewOut)
def create_review_route(
    school_id: int,
    data: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_review(db, school_id, data, current_user)


@router.delete("/reviews/{review_id}")
def delete_review_route(
    review_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return delete_review(db, review_id, current_user)
